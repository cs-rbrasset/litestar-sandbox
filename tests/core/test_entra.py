"""core/entra.py: o backend como resource server. verify_access_token é testado contra um
par RSA gerado na hora e um JWKS fake (niquests.AsyncSession.get monkeypatchado) — sem rede,
sem depender do Entra de verdade, mas exercitando a mesma validação de assinatura/iss/aud.
"""

import asyncio
import base64
from typing import TYPE_CHECKING, Any

import jwt
import niquests
from cryptography.hazmat.primitives.asymmetric import rsa

from litestar_sandbox.core import entra

if TYPE_CHECKING:
    import pytest

KID = "test-kid-1"
TENANT_ID = "tenant-x"
AUDIENCE = "api://client-x"


def _rsa_keypair() -> tuple[Any, dict[str, Any]]:
    """Chave privada (pra assinar) + o JWK público equivalente (pro JWKS fake)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()

    def _b64(n: int) -> str:
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode("ascii")

    jwk = {
        "kty": "RSA",
        "kid": KID,
        "use": "sig",
        "n": _b64(public_numbers.n),
        "e": _b64(public_numbers.e),
    }
    return private_key, jwk


def _fake_jwks(monkeypatch: pytest.MonkeyPatch, jwk: dict[str, Any]) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"keys": [jwk]}

    async def fake_get(self: niquests.AsyncSession, url: str) -> FakeResponse:
        assert url == f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
        return FakeResponse()

    monkeypatch.setattr(niquests.AsyncSession, "get", fake_get)
    entra._jwks_cache.clear()


def test_entra_settings_from_env_is_none_without_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENTRA_TENANT_ID", raising=False)
    assert entra.EntraSettings.from_env() is None


def test_entra_settings_from_env_reads_all_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENTRA_TENANT_ID", TENANT_ID)
    monkeypatch.setenv("ENTRA_API_AUDIENCE", AUDIENCE)
    settings = entra.EntraSettings.from_env()
    assert settings is not None
    assert settings.audience == AUDIENCE
    assert settings.issuer == f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
    assert settings.jwks_uri == f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"


def test_identity_from_claims_lowercases_oid_into_db_role() -> None:
    identity = entra.identity_from_claims({"oid": "ABCD-1234", "name": "Alice Teste"})
    assert identity.subject == "abcd-1234"
    assert identity.db_role == "u_abcd-1234"
    assert identity.name == "Alice Teste"


def test_identity_from_claims_falls_back_to_preferred_username() -> None:
    identity = entra.identity_from_claims({"oid": "x", "preferred_username": "alice@gestora"})
    assert identity.name == "alice@gestora"


def test_verify_access_token_accepts_valid_signature_issuer_and_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, jwk = _rsa_keypair()
    _fake_jwks(monkeypatch, jwk)
    settings = entra.EntraSettings(tenant_id=TENANT_ID, audience=AUDIENCE)
    token = jwt.encode(
        {"oid": "abcd-1234", "name": "Alice Teste", "aud": AUDIENCE, "iss": settings.issuer},
        private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    claims = asyncio.run(entra.verify_access_token(settings, token))
    assert claims["oid"] == "abcd-1234"


def test_verify_access_token_rejects_wrong_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, jwk = _rsa_keypair()
    _fake_jwks(monkeypatch, jwk)
    settings = entra.EntraSettings(tenant_id=TENANT_ID, audience=AUDIENCE)
    token = jwt.encode(
        {"oid": "abcd-1234", "aud": "api://outro-client", "iss": settings.issuer},
        private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    try:
        asyncio.run(entra.verify_access_token(settings, token))
    except jwt.InvalidAudienceError:
        pass
    else:
        msg = "esperava jwt.InvalidAudienceError"
        raise AssertionError(msg)


def test_verify_access_token_rejects_signature_from_another_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, jwk = _rsa_keypair()  # o JWKS fake só tem essa chave pública
    _fake_jwks(monkeypatch, jwk)
    other_private_key, _ = _rsa_keypair()  # mas o token é assinado por outra
    settings = entra.EntraSettings(tenant_id=TENANT_ID, audience=AUDIENCE)
    token = jwt.encode(
        {"oid": "abcd-1234", "aud": AUDIENCE, "iss": settings.issuer},
        other_private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    try:
        asyncio.run(entra.verify_access_token(settings, token))
    except jwt.InvalidSignatureError:
        pass
    else:
        msg = "esperava jwt.InvalidSignatureError"
        raise AssertionError(msg)
