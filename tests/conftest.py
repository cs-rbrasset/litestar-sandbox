from typing import TYPE_CHECKING, Any

import pytest
from litestar.testing import TestClient

from litestar_sandbox.app import create_app
from litestar_sandbox.core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    import httpx
    from litestar import Litestar

FUND_CNPJ = "12345678000190"


@pytest.fixture
def database_settings(tmp_path: Path) -> DatabaseSettings:
    return DatabaseSettings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def app(database_settings: DatabaseSettings) -> Litestar:
    return create_app(database_settings)


@pytest.fixture
def app_client(app: Litestar) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app) as client:
        yield client


@pytest.fixture
def create_instrument(app_client: TestClient[Litestar]) -> Callable[..., dict[str, Any]]:
    def _create(**overrides: str) -> dict[str, Any]:
        payload = {"name": "caneta azul", "cetip_code": "CANE4", "instrument_type": "CRI"}
        response = app_client.post("/api/v1/instruments", data=payload | overrides)
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
        return app_client.post("/api/v1/trades", json=payload | overrides)

    return _post
