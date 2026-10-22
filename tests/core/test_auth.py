import asyncio
from typing import TYPE_CHECKING

import pytest
from litestar import Litestar, Request, Router, get
from litestar.testing import AsyncTestClient, TestClient

from litestar_sandbox.core.auth import AuthMiddleware, DevTokenVerifier
from litestar_sandbox.core.identity import Identity, current_identity, current_trace_id

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
        "request_user": request.user.db_role,
        "trace_id": current_trace_id.get(),
    }


@get("/ping")
async def ping() -> str:
    return "pong"


@get("/")
async def spa_root() -> str:
    return "spa"


@pytest.fixture
def client() -> Iterator[TestClient[Litestar]]:
    app = Litestar(
        route_handlers=[Router("/api/v1", route_handlers=[whoami, ping]), spa_root],
        middleware=[AuthMiddleware(DevTokenVerifier({"a": ALICE, "b": BOB}), "/api/v1")],
    )
    with TestClient(app) as test_client:
        yield test_client


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_is_401(client: TestClient[Litestar]) -> None:
    response = client.get("/api/v1/whoami")
    assert response.status_code == 401
    assert response.json()["detail"] == "token ausente"


@pytest.mark.parametrize("header", ["Bearer nao-existe", "Basic YTpi", "Bearer ", "a"])
def test_invalid_authorization_is_401(client: TestClient[Litestar], header: str) -> None:
    assert client.get("/api/v1/whoami", headers={"Authorization": header}).status_code == 401


def test_valid_token_opens_identity_context(client: TestClient[Litestar]) -> None:
    body = client.get("/api/v1/whoami", headers=bearer("a") | {"X-Request-ID": "req-123"}).json()
    assert body == {"context": "u_alice", "request_user": "u_alice", "trace_id": "req-123"}


def test_trace_id_is_generated_when_absent(client: TestClient[Litestar]) -> None:
    assert len(client.get("/api/v1/whoami", headers=bearer("a")).json()["trace_id"]) == 32


@pytest.mark.parametrize("path", ["/api/v1/ping", "/"])
def test_public_paths_skip_auth(client: TestClient[Litestar], path: str) -> None:
    assert client.get(path).status_code == 200


def test_identity_does_not_leak_between_requests(client: TestClient[Litestar]) -> None:
    """O teste do handoff: duas pessoas no mesmo worker, cada uma vê só a própria identidade."""
    for token, role in [("a", "u_alice"), ("b", "u_bob"), ("a", "u_alice")]:
        assert client.get("/api/v1/whoami", headers=bearer(token)).json()["context"] == role
    assert current_identity.get() is None


@pytest.mark.anyio
async def test_concurrent_requests_keep_their_own_identity() -> None:
    app = Litestar(
        route_handlers=[Router("/api/v1", route_handlers=[whoami])],
        middleware=[AuthMiddleware(DevTokenVerifier({"a": ALICE, "b": BOB}), "/api/v1")],
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
