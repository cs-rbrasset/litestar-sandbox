"""Autenticação: valida o token, identifica a pessoa e abre o contexto da requisição.

O verificador é plugável. Hoje existe só o DevTokenVerifier (tokens fixos, para dev e testes);
o verificador do Entra ID (JWT RS256 validado contra o JWKS do tenant) entra no mesmo lugar.
"""

import os
import uuid
from typing import TYPE_CHECKING, Protocol

from litestar.exceptions import NotAuthorizedException
from litestar.middleware import ASGIMiddleware

from litestar_sandbox.core.identity import Identity, use_identity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from litestar.types import ASGIApp, Receive, Scope, Send


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
