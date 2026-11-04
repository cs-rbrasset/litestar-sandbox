from typing import TYPE_CHECKING, Any

import pytest
from litestar.testing import TestClient

from app import create_app
from core.auth import DevTokenVerifier
from core.identity import Identity
from core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    import httpx
    from litestar import Litestar

FUND_CNPJ = "12345678000190"


@pytest.fixture
def database_settings(tmp_path: Path) -> DatabaseSettings:
    return DatabaseSettings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")


TEST_TOKEN = "token-de-teste"
TEST_IDENTITY = Identity(subject="u_teste", db_role="u_teste", name="Pessoa de Teste")


@pytest.fixture
def app(database_settings: DatabaseSettings) -> Litestar:
    return create_app(database_settings, verifier=DevTokenVerifier({TEST_TOKEN: TEST_IDENTITY}))


@pytest.fixture
def app_client(app: Litestar) -> Iterator[TestClient[Litestar]]:
    """Cliente já autenticado: os testes de negócio não repetem o token."""
    with TestClient(app=app) as client:
        client.headers["Authorization"] = f"Bearer {TEST_TOKEN}"
        yield client


@pytest.fixture
def create_instrument(app_client: TestClient[Litestar]) -> Callable[..., dict[str, Any]]:
    def _create(**overrides: str) -> dict[str, Any]:
        payload = {"name": "caneta azul", "cetip_code": "CANE4", "instrument_type": "CRI"}
        response = app_client.post("/api/v1/ativos", data=payload | overrides)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def post_trade(app_client: TestClient[Litestar]) -> Callable[..., httpx.Response]:
    def _post(instrument_id: int, **overrides: Any) -> httpx.Response:
        payload = {
            "fund_cnpj": FUND_CNPJ,
            "instrument_id": instrument_id,
            "trade_date": "2026-10-01",
            "side": "BUY",
            "quantity": 100,
            "unit_price": "101.25",
        }
        return app_client.post("/api/v1/boletas", json=payload | overrides)

    return _post
