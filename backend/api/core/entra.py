"""Backend como resource server do Entra ID: só valida o access_token que o front já traz.

Quem fala com o Entra (login, PKCE, refresh) é o front — @azure/msal-browser, cliente
público (SPA), sem secret. O backend nunca vê client_secret nem redirect_uri de ninguém: só
confere a assinatura RS256 contra o JWKS do tenant, o emissor e a audiência. Com "Expose an
API" feito no Entra (scope access_as_user), o front pede o access_token com esse scope
(web-svelte-kit/src/shared/auth/msal.ts: LOGIN_SCOPES) e a audiência é o próprio client_id.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import jwt
import niquests
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import text

from core.identity import DB_ROLE_PATTERN, Identity

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

_HTTP_TIMEOUT = 30.0


@dataclass(frozen=True)
class EntraSettings:
    tenant_id: str
    # client_id do App registration (SPA): o scope access_as_user de "Expose an API" usa
    # "api://<client_id>/access_as_user", mas o claim "aud" do access_token continua sendo
    # o client_id puro — é esse valor que entra aqui.
    audience: str

    @classmethod
    def from_env(cls) -> EntraSettings | None:
        """None quando ENTRA_TENANT_ID não está setado: a validação via Entra fica desligada."""
        tenant_id = os.getenv("ENTRA_TENANT_ID")
        if not tenant_id:
            return None
        return cls(tenant_id=tenant_id, audience=os.environ["ENTRA_API_AUDIENCE"])

    @property
    def issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

    @property
    def jwks_uri(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"


# kid -> chave pública RSA. Sem TTL: a rotação de chave do Entra é rara o bastante pra
# reiniciar o worker ser mitigação aceitável.
_jwks_cache: dict[str, Any] = {}


async def _public_key(settings: EntraSettings, kid: str) -> Any:
    if kid not in _jwks_cache:
        async with niquests.AsyncSession(timeout=_HTTP_TIMEOUT) as session:
            response = await session.get(settings.jwks_uri)
            response.raise_for_status()
        for jwk in response.json()["keys"]:
            _jwks_cache[jwk["kid"]] = RSAAlgorithm.from_jwk(jwk)
    return _jwks_cache[kid]


async def verify_access_token(settings: EntraSettings, access_token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(access_token)
    key = await _public_key(settings, header["kid"])
    return jwt.decode(
        access_token,
        key=key,
        algorithms=["RS256"],
        audience=settings.audience,
        issuer=settings.issuer,
        leeway=30,
    )


def identity_from_claims(claims: dict[str, Any]) -> Identity:
    """u_<object id> (core/identity.py, DB_ROLE_PATTERN) — oid do Entra é um GUID minúsculo."""
    oid = str(claims["oid"]).lower()
    db_role = f"u_{oid}"
    if not DB_ROLE_PATTERN.fullmatch(db_role):
        msg = f"oid do Entra gerou role inválida: {db_role!r}"
        raise ValueError(msg)
    name = claims.get("name") or claims.get("preferred_username") or oid
    return Identity(subject=oid, db_role=db_role, name=str(name))


async def ensure_person_role(engine: AsyncEngine, db_role: str) -> None:
    """Job de espelhamento (db/identity_mirror.sql): cria a role no primeiro login.

    Sem isso, app.assumir_identidade(db_role) falha com "role ... does not exist" — um
    erro que o advanced-alchemy converte em 409 (IntegrityError), sem relação com conflito
    de dado nenhum. No SQLite (testes) a função não existe: ensure_person_role não é
    chamada lá (EntraTokenVerifier só a chama quando há database_url de Postgres).
    """
    async with engine.begin() as conn:
        await conn.execute(text("select app.garantir_pessoa(:role)"), {"role": db_role})
