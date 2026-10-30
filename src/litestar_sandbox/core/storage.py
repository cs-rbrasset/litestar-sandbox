"""Object storage via API REST do Supabase Storage — não é a conexão do Postgres.

Credenciais diferentes de propósito: a service_role key autentica na API do Storage, nunca
no Postgres, e nunca pode chegar ao front (só o backend/worker a usam).
"""

from typing import TYPE_CHECKING

import niquests

if TYPE_CHECKING:
    from litestar_sandbox.core.settings import SupabaseSettings

# o default do niquests (5s) já estourou uma vez num upload real; a API do Storage é externa
_TIMEOUT = 30.0


async def upload_object(settings: SupabaseSettings, path: str, content: bytes, content_type: str) -> None:
    url = f"{settings.url}/storage/v1/object/{settings.bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.service_role_key}",
        "apikey": settings.service_role_key,
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    async with niquests.AsyncSession(timeout=_TIMEOUT) as session:
        response = await session.post(url, headers=headers, data=content)
        response.raise_for_status()


async def create_signed_url(settings: SupabaseSettings, path: str, expires_in: int = 3600) -> str:
    url = f"{settings.url}/storage/v1/object/sign/{settings.bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.service_role_key}",
        "apikey": settings.service_role_key,
    }
    async with niquests.AsyncSession(timeout=_TIMEOUT) as session:
        response = await session.post(url, headers=headers, json={"expiresIn": expires_in})
        response.raise_for_status()
        signed_path = response.json()["signedURL"]
    return f"{settings.url}/storage/v1{signed_path}"
