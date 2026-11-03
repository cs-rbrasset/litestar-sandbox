import asyncio
from typing import TYPE_CHECKING

import jwt
import pytest
from litestar import Litestar, Request, Router, get
from litestar.testing import AsyncTestClient, TestClient

from litestar_sandbox.core import entra
from litestar_sandbox.core.auth import (
    CompositeVerifier,
    DevTokenVerifier,
    EntraTokenVerifier,
    build_verifier,
)
from litestar_sandbox.core.identity import Identity, current_identity, current_trace_id
from litestar_sandbox.core.security import IdentityBridgePlugin, create_security_plugin

if TYPE_CHECKING:
    from collections.abc import Iterator

ALICE = Identity(subject="u_alice", db_role="u_alice", name="Alice")
BOB = Identity(subject="u_bob", db_role="u_bob", name="Bob")


@get("/whoami")
async def whoami(request: Request) -> dict[str, str | None]:
    identity = current_identity.get()
    await asyncio.sleep(0.01)  # dá chance a outra requisição intercalar
    return {
        "context": identity.db_role if identity else None,
        # request.user é o Principal[Identity] que o SecurityPlugin resolveu; .user é a
        # Identity de verdade (core/security.py: _IdentityResolver).
        "request_user": request.user.user.db_role,
        "trace_id": current_trace_id.get(),
    }


@get("/ping")
async def ping() -> str:
    return "pong"


@pytest.fixture
def client() -> Iterator[TestClient[Litestar]]:
    verifier = DevTokenVerifier({"a": ALICE, "b": BOB})
    app = Litestar(
        route_handlers=[Router("/api/v1", route_handlers=[whoami, ping])],
        plugins=[create_security_plugin(verifier, "/api/v1"), IdentityBridgePlugin()],
    )
    with TestClient(app) as test_client:
        yield test_client


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_is_401(client: TestClient[Litestar]) -> None:
    assert client.get("/api/v1/whoami").status_code == 401


@pytest.mark.parametrize("header", ["Bearer nao-existe", "Basic YTpi", "Bearer ", "a"])
def test_invalid_authorization_is_401(client: TestClient[Litestar], header: str) -> None:
    assert client.get("/api/v1/whoami", headers={"Authorization": header}).status_code == 401


def test_valid_token_opens_identity_context(client: TestClient[Litestar]) -> None:
    body = client.get("/api/v1/whoami", headers=bearer("a") | {"X-Request-ID": "req-123"}).json()
    assert body == {"context": "u_alice", "request_user": "u_alice", "trace_id": "req-123"}


def test_trace_id_is_generated_when_absent(client: TestClient[Litestar]) -> None:
    assert len(client.get("/api/v1/whoami", headers=bearer("a")).json()["trace_id"]) == 32


def test_public_paths_skip_auth(client: TestClient[Litestar]) -> None:
    assert client.get("/api/v1/ping").status_code == 200


def test_identity_does_not_leak_between_requests(client: TestClient[Litestar]) -> None:
    """O teste do handoff: duas pessoas no mesmo worker, cada uma vê só a própria identidade."""
    for token, role in [("a", "u_alice"), ("b", "u_bob"), ("a", "u_alice")]:
        assert client.get("/api/v1/whoami", headers=bearer(token)).json()["context"] == role
    assert current_identity.get() is None


@pytest.mark.anyio
async def test_concurrent_requests_keep_their_own_identity() -> None:
    verifier = DevTokenVerifier({"a": ALICE, "b": BOB})
    app = Litestar(
        route_handlers=[Router("/api/v1", route_handlers=[whoami])],
        plugins=[create_security_plugin(verifier, "/api/v1"), IdentityBridgePlugin()],
    )
    async with AsyncTestClient(app) as async_client:
        tokens = ["a", "b"] * 10
        responses = await asyncio.gather(
            *(async_client.get("/api/v1/whoami", headers=bearer(t)) for t in tokens)
        )
    roles = [r.json()["context"] for r in responses]
    assert roles == [{"a": "u_alice", "b": "u_bob"}[t] for t in tokens]


def test_dev_tokens_from_env_format() -> None:
    verifier = DevTokenVerifier.from_env("t1=u_alice:Alice, t2=app_sistema")
    assert asyncio.run(verifier.verify("t1")) == Identity("u_alice", "u_alice", "Alice")
    assert asyncio.run(verifier.verify("t2")) == Identity(
        "app_sistema", "app_sistema", "app_sistema"
    )
    assert asyncio.run(verifier.verify("t3")) is None


def test_empty_dev_tokens_let_nobody_in() -> None:
    assert asyncio.run(DevTokenVerifier.from_env("").verify("qualquer")) is None


@pytest.mark.parametrize("role", ["postgres", "u_alice; drop table trade", "U_ALICE", ""])
def test_identity_rejects_unknown_role_formats(role: str) -> None:
    with pytest.raises(ValueError, match="db_role inválida"):
        Identity(subject="x", db_role=role, name="x")


def test_entra_token_verifier_accepts_valid_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")

    async def fake_verify(s: entra.EntraSettings, token: str) -> dict[str, str]:
        assert s is settings
        assert token == "access-token"
        return {"oid": "ABCD-1234", "name": "Alice Teste"}

    monkeypatch.setattr(entra, "verify_access_token", fake_verify)
    identity = asyncio.run(EntraTokenVerifier(settings).verify("access-token"))
    assert identity == Identity(subject="abcd-1234", db_role="u_abcd-1234", name="Alice Teste")


def test_entra_token_verifier_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")

    async def fake_verify(s: entra.EntraSettings, token: str) -> dict[str, str]:
        raise jwt.InvalidTokenError

    monkeypatch.setattr(entra, "verify_access_token", fake_verify)
    assert asyncio.run(EntraTokenVerifier(settings).verify("lixo")) is None


def test_entra_token_verifier_rejects_claims_without_oid(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")

    async def fake_verify(s: entra.EntraSettings, token: str) -> dict[str, str]:
        return {"name": "Alice Teste"}  # sem "oid"

    monkeypatch.setattr(entra, "verify_access_token", fake_verify)
    assert asyncio.run(EntraTokenVerifier(settings).verify("sem-oid")) is None


POSTGRES_URL = "postgresql+asyncpg://u:p@localhost/db"


def _fake_verify_for(oid: str):  # mesma assinatura de entra.verify_access_token
    async def fake_verify(s: entra.EntraSettings, token: str) -> dict[str, str]:
        return {"oid": oid, "name": "Alice Teste"}

    return fake_verify


def test_entra_token_verifier_ensures_role_on_first_login(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra, "verify_access_token", _fake_verify_for("abcd"))
    calls: list[str] = []

    async def fake_ensure(engine: object, db_role: str) -> None:
        calls.append(db_role)

    monkeypatch.setattr(entra, "ensure_person_role", fake_ensure)
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")
    verifier = EntraTokenVerifier(settings, POSTGRES_URL)
    identity = asyncio.run(verifier.verify("tok"))
    assert identity == Identity("abcd", "u_abcd", "Alice Teste")
    assert calls == ["u_abcd"]


def test_entra_token_verifier_ensures_role_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entra, "verify_access_token", _fake_verify_for("abcd"))
    calls: list[str] = []

    async def fake_ensure(engine: object, db_role: str) -> None:
        calls.append(db_role)

    monkeypatch.setattr(entra, "ensure_person_role", fake_ensure)
    verifier = EntraTokenVerifier(
        entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x"), POSTGRES_URL
    )
    asyncio.run(verifier.verify("tok"))
    asyncio.run(verifier.verify("tok"))
    assert calls == ["u_abcd"]  # segunda vez: já tá no cache, não bate no Postgres de novo


def test_entra_token_verifier_skips_role_ensure_without_postgres_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(entra, "verify_access_token", _fake_verify_for("abcd"))

    async def fake_ensure(engine: object, db_role: str) -> None:
        msg = "não deveria ter sido chamado"
        raise AssertionError(msg)

    monkeypatch.setattr(entra, "ensure_person_role", fake_ensure)
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")
    for url in (None, "sqlite+aiosqlite:///./sandbox.db"):
        identity = asyncio.run(EntraTokenVerifier(settings, url).verify("tok"))
        assert identity == Identity("abcd", "u_abcd", "Alice Teste")


def test_entra_token_verifier_role_ensure_failure_does_not_block_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(entra, "verify_access_token", _fake_verify_for("abcd"))

    async def fake_ensure(engine: object, db_role: str) -> None:
        msg = "sem CREATEROLE"
        raise RuntimeError(msg)

    monkeypatch.setattr(entra, "ensure_person_role", fake_ensure)
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")
    identity = asyncio.run(EntraTokenVerifier(settings, POSTGRES_URL).verify("tok"))
    assert identity == Identity("abcd", "u_abcd", "Alice Teste")


def test_composite_verifier_tries_each_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = entra.EntraSettings(tenant_id="tenant-x", audience="api://client-x")

    async def fake_verify(s: entra.EntraSettings, token: str) -> dict[str, str]:
        if token != "access-token":
            raise jwt.InvalidTokenError
        return {"oid": "a", "name": "Alice"}

    monkeypatch.setattr(entra, "verify_access_token", fake_verify)
    composite = CompositeVerifier(DevTokenVerifier({"dev-bob": BOB}), EntraTokenVerifier(settings))
    assert asyncio.run(composite.verify("dev-bob")) == BOB
    assert asyncio.run(composite.verify("access-token")) == Identity("a", "u_a", "Alice")
    assert asyncio.run(composite.verify("nem-um-nem-outro")) is None


def test_build_verifier_is_dev_only_without_entra_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENTRA_TENANT_ID", raising=False)
    monkeypatch.setenv("AUTH_DEV_TOKENS", "tok-alice=u_alice:Alice")
    verifier = build_verifier()
    assert isinstance(verifier, DevTokenVerifier)


def test_build_verifier_adds_entra_verifier_when_tenant_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENTRA_TENANT_ID", "tenant-x")
    monkeypatch.setenv("ENTRA_API_AUDIENCE", "api://client-x")
    monkeypatch.setenv("AUTH_DEV_TOKENS", "")
    verifier = build_verifier()
    assert isinstance(verifier, CompositeVerifier)
