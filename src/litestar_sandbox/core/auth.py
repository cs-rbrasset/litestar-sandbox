"""Autenticação: valida o token, identifica a pessoa e abre o contexto da requisição.

O verificador é plugável e composto: DevTokenVerifier (tokens fixos, dev e testes) sempre
ativo, EntraTokenVerifier (access_token do Entra ID, validado contra o JWKS do tenant) ativo
quando ENTRA_TENANT_ID está setado. A credencial sempre chega por `Authorization: Bearer` —
o front (web-svelte-kit/) já pede o token com MSAL.js e o anexa na chamada; o backend nunca
fala com o Entra pra login.
"""

import logging
import os
import uuid
from typing import TYPE_CHECKING, Protocol

from litestar.exceptions import NotAuthorizedException
from litestar.middleware import ASGIMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from litestar_sandbox.core import entra
from litestar_sandbox.core.identity import Identity, use_identity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from litestar.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class TokenVerifier(Protocol):
    async def verify(self, token: str) -> Identity | None: ...


class DevTokenVerifier:
    """Tokens fixos mapeados para identidades. Só para dev e testes."""

    def __init__(self, tokens: Mapping[str, Identity]) -> None:
        self._tokens = dict(tokens)

    async def verify(self, token: str) -> Identity | None:
        return self._tokens.get(token)

    @classmethod
    def from_env(cls, value: str | None = None) -> DevTokenVerifier:
        """AUTH_DEV_TOKENS="token=db_role:Nome,outro=db_role:Nome". Vazio: ninguém entra."""
        raw = os.getenv("AUTH_DEV_TOKENS", "") if value is None else value
        tokens: dict[str, Identity] = {}
        for entry in filter(None, (part.strip() for part in raw.split(","))):
            token, _, rest = entry.partition("=")
            db_role, _, name = rest.partition(":")
            tokens[token] = Identity(subject=db_role, db_role=db_role, name=name or db_role)
        return cls(tokens)


class EntraTokenVerifier:
    """Valida o access_token que o front pediu ao Entra (core/entra.py).

    Resource server puro: não troca código, não emite cookie, não guarda estado nenhum —
    só confere assinatura RS256, emissor e audiência a cada request contra o JWKS do tenant.
    No primeiro login de cada pessoa, garante a role dela no Postgres (ensure_person_role) —
    sem isso, a identidade é válida mas a primeira transação falha no SET LOCAL ROLE.
    """

    def __init__(self, settings: entra.EntraSettings, database_url: str | None = None) -> None:
        self._settings = settings
        # garantir_pessoa() só existe no Postgres (db/identity_mirror.sql); no SQLite dos
        # testes a role nem faz sentido — fica desligado, não só sem efeito.
        self._database_url = database_url if database_url and "postgresql" in database_url else None
        self._engine: AsyncEngine | None = None
        self._ensured_roles: set[str] = set()

    def _role_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(self._database_url)  # type: ignore[arg-type]
        return self._engine

    async def _ensure_role(self, db_role: str) -> None:
        if self._database_url is None or db_role in self._ensured_roles:
            return
        try:
            await entra.ensure_person_role(self._role_engine(), db_role)
        except Exception:
            # não impede o login: a pessoa só não consegue gravar nada até isso resolver,
            # e o erro real (sem CREATEROLE, schema errado) fica aqui, não num 401 genérico.
            logger.exception("não deu pra garantir a role %s no Postgres", db_role)
            return
        self._ensured_roles.add(db_role)

    async def verify(self, token: str) -> Identity | None:
        try:
            claims = await entra.verify_access_token(self._settings, token)
        except Exception:
            # 401 pro cliente não diz o motivo; o motivo real (aud errado, iss errado,
            # assinatura, JWKS fora do ar) só aparece aqui, no terminal do backend.
            logger.warning("token do Entra recusado", exc_info=True)
            return None
        try:
            identity = entra.identity_from_claims(claims)
        except (KeyError, ValueError):
            logger.warning("claims do Entra sem oid utilizável: %r", claims)
            return None
        await self._ensure_role(identity.db_role)
        return identity


class CompositeVerifier:
    """Tenta cada verificador em ordem; o primeiro que reconhecer o token vence."""

    def __init__(self, *verifiers: TokenVerifier) -> None:
        self._verifiers = verifiers

    async def verify(self, token: str) -> Identity | None:
        for verifier in self._verifiers:
            identity = await verifier.verify(token)
            if identity is not None:
                return identity
        return None


def build_verifier(database_url: str | None = None) -> TokenVerifier:
    """DevTokenVerifier sempre ativo; EntraTokenVerifier só se ENTRA_TENANT_ID estiver
    setado — sem ele, token do Entra é recusado e só token de dev funciona. database_url
    é pro espelhamento de role (ensure_person_role); sem ele (ou fora do Postgres), login
    funciona mas quem logar pela primeira vez não consegue gravar nada ainda.
    """
    verifiers: list[TokenVerifier] = [DevTokenVerifier.from_env()]
    settings = entra.EntraSettings.from_env()
    if settings is not None:
        verifiers.append(EntraTokenVerifier(settings, database_url))
    return verifiers[0] if len(verifiers) == 1 else CompositeVerifier(*verifiers)


def _bearer_token(scope: Scope) -> str | None:
    for key, value in scope["headers"]:
        if key == b"authorization":
            scheme, _, token = value.decode("latin-1").partition(" ")
            if scheme.lower() != "bearer":
                return None
            return token.strip() or None
    return None


def _request_id(scope: Scope) -> str:
    for key, value in scope["headers"]:
        if key == b"x-request-id":
            return value.decode("latin-1")[:64]
    return uuid.uuid4().hex


class AuthMiddleware(ASGIMiddleware):
    """Exige `Authorization: Bearer <token>` na API e abre o contexto de identidade.

    A SPA, os assets, o OpenAPI e o /ping ficam de fora. A identidade vale só durante a
    requisição: use_identity() restaura o contexto ao sair, então nada vaza para a próxima.
    """

    def __init__(self, verifier: TokenVerifier, api_prefix: str) -> None:
        self.verifier = verifier
        self.exclude_path_pattern = (
            rf"^(?!{api_prefix}/)",  # tudo fora da API: SPA, /static
            rf"^{api_prefix}/ping$",
            rf"^{api_prefix}/schema",
        )

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        token = _bearer_token(scope)
        if token is None:
            raise NotAuthorizedException(detail="token ausente")
        identity = await self.verifier.verify(token)
        if identity is None:
            raise NotAuthorizedException(detail="token inválido")
        scope["user"] = identity
        with use_identity(identity, trace_id=_request_id(scope)):
            await next_app(scope, receive, send)
