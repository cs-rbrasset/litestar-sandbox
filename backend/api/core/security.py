"""Ponte entre o TokenVerifier existente (core/auth.py) e o SecurityPlugin.

A verificação de verdade não muda: DevTokenVerifier/EntraTokenVerifier/CompositeVerifier
continuam fazendo o trabalho (já revisados). Esse módulo só embrulha um TokenVerifier
qualquer num único AuthenticationMechanism, pra ganhar do SecurityPlugin: headers de
segurança (SecurityHeadersConfig.hardened()) e o schema Bearer consistente no OpenAPI (dono
único — SecurityPlugin recusa coexistir com `OpenAPIConfig(security=...)` manual).

A identidade resolvida chega em `scope["user"]` (convenção nativa do Litestar — mesma coisa
que `connection.user`/`.auth`, usada pelo próprio `AbstractAuthenticationMiddleware`).
IdentityBridgeMiddleware lê isso logo depois do SecurityMiddlewareWrapper e abre
use_identity() — mesmo contrato do AuthMiddleware antigo (SET LOCAL ROLE via
core/database.py), só que a identidade já chega pronta em vez de o middleware validar o
token ele mesmo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from litestar.middleware import ASGIMiddleware
from litestar.openapi.spec import SecurityScheme
from litestar.plugins import InitPlugin
from litestar_security import SecurityConfig, SecurityPlugin
from litestar_security.authentication import (
    Authenticated,
    AuthenticationEvidence,
    AuthenticationMechanism,
    InvalidCredentials,
    NoCredentials,
    PresentedCredential,
    Principal,
)
from litestar_security.headers import SecurityHeadersConfig

from core.identity import use_identity

if TYPE_CHECKING:
    from litestar.config.app import AppConfig
    from litestar.connection import ASGIConnection
    from litestar.types import ASGIApp, Receive, Scope, Send
    from litestar_security.authentication import (
        AuthenticationOutcome,
        CredentialExtraction,
        IdentityResolution,
    )

    from core.auth import TokenVerifier
    from core.identity import Identity

_SLOT_NAME = "authorization.bearer"


@dataclass(frozen=True, slots=True)
class _BearerSlot:
    """Extrai o token de `Authorization: Bearer <token>` — mesma regra do `_bearer_token`
    antigo (core/auth.py), síncrona porque o Protocol CredentialSlot exige (roda em toda
    requisição, sem I/O).
    """

    name: str = _SLOT_NAME

    def extract(self, connection: ASGIConnection[Any, Any, Any, Any]) -> CredentialExtraction[str]:
        header = connection.headers.get("Authorization")
        if not header:
            return NoCredentials()
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return InvalidCredentials(code="malformed_bearer")
        return PresentedCredential(value=token.strip())


@dataclass(frozen=True, slots=True)
class _TokenVerifierAuthenticator:
    """authenticator: delega pro TokenVerifier existente — a verificação (JWKS, assinatura,
    tokens fixos de dev) não muda, só ganha a casca que o SecurityPlugin espera."""

    verifier: TokenVerifier
    name: str = "bearer"
    slot: str = _SLOT_NAME
    participates_by_default: bool = True

    async def authenticate(
        self, credential: str, connection: ASGIConnection[Any, Any, Any, Any]
    ) -> AuthenticationOutcome[Identity]:
        identity = await self.verifier.verify(credential)
        if identity is None:
            return InvalidCredentials(code="invalid_token")
        return Authenticated(
            claims=identity,
            evidence=AuthenticationEvidence(
                mechanism=self.name, slot=self.slot, authenticated_at=datetime.now(UTC)
            ),
        )


@dataclass(frozen=True, slots=True)
class _IdentityResolver:
    """resolver: os claims já SÃO a Identity (o authenticator acima resolveu tudo); só
    embrulha no Principal que o SecurityPlugin espera."""

    async def resolve(self, claims: Identity) -> IdentityResolution[Identity]:
        return Principal(id=claims.subject, display_name=claims.name, user=claims)


def create_security_plugin(verifier: TokenVerifier, api_prefix: str) -> SecurityPlugin:
    mechanism = AuthenticationMechanism(
        authenticator=_TokenVerifierAuthenticator(verifier),
        resolver=_IdentityResolver(),
        scheme_name="BearerToken",
        security_scheme=SecurityScheme(type="http", scheme="bearer"),
    )
    return SecurityPlugin(
        SecurityConfig(
            slots=(_BearerSlot(),),
            mechanisms=(mechanism,),
            # /ping fica de fora; /schema já é público por padrão do próprio SecurityPlugin
            # (nunca liste rotas de OpenAPI aqui — ele recusa no startup).
            exclude=[rf"^{api_prefix}/ping$"],
            headers=SecurityHeadersConfig.hardened(),
        )
    )


def _request_id(scope: Scope) -> str:
    for key, value in scope["headers"]:
        if key == b"x-request-id":
            return value.decode("latin-1")[:64]
    return uuid.uuid4().hex


class IdentityBridgeMiddleware(ASGIMiddleware):
    """Lê a identidade que o SecurityPlugin já resolveu (`scope["user"]`) e abre
    use_identity() — nada a verificar aqui, só abrir/fechar o contexto pro resto do
    pipeline (core/database.py: SET LOCAL ROLE por transação).
    """

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        principal = scope.get("user")
        identity = getattr(principal, "user", None) if principal is not None else None
        if identity is None:
            await next_app(scope, receive, send)
            return
        with use_identity(identity, trace_id=_request_id(scope)):
            await next_app(scope, receive, send)


class IdentityBridgePlugin(InitPlugin):
    """Registra IdentityBridgeMiddleware no fim da lista (app_config.middleware), não no
    construtor do Litestar: o SecurityPlugin insere o próprio middleware durante o
    on_app_init dele, numa posição calculada a partir do que já está na lista naquele
    momento. Se a nossa ponte entrasse direto em Litestar(middleware=[...]), ela ficaria
    ANTES do SecurityMiddlewareWrapper na cadeia (mais externa) e rodaria antes de
    scope["user"] existir — plugin aqui, depois do create_security_plugin() na lista de
    plugins, garante a ordem certa.
    """

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.middleware.append(IdentityBridgeMiddleware())
        return app_config
