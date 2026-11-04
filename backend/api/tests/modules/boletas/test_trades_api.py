import decimal
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx
    from litestar import Litestar
    from litestar.testing import TestClient

    CreateInstrument = Callable[..., dict[str, Any]]
    PostTrade = Callable[..., httpx.Response]


@pytest.fixture
def instrument(create_instrument: CreateInstrument) -> dict[str, Any]:
    return create_instrument(cetip_code="ABCD4")


@pytest.fixture
def trade(instrument: dict[str, Any], post_trade: PostTrade) -> dict[str, Any]:
    response = post_trade(instrument["id"])
    assert response.status_code == 201, response.text
    return response.json()


def test_create_trade_starts_pending_and_copies_cetip_code(trade: dict[str, Any]) -> None:
    assert trade["status"] == "PENDING"
    assert trade["cetip_code"] == "ABCD4"
    assert trade["quantity"] == 100
    # Numeric(20, 8): o preço volta com 8 casas ("101.25000000")
    assert decimal.Decimal(trade["unit_price"]) == decimal.Decimal("101.25")


@pytest.mark.parametrize(
    "overrides",
    [
        {"fund_cnpj": "1234567800019"},
        {"fund_cnpj": "12.345.678/0001-90"},
        {"quantity": 0},
        {"quantity": -5},
        {"unit_price": "0"},
        {"unit_price": "-1"},
        {"side": "HOLD"},
        {"trade_date": "2026-13-01"},
    ],
    ids=[
        "cnpj-13-digitos",
        "cnpj-formatado",
        "quantidade-zero",
        "quantidade-negativa",
        "preco-zero",
        "preco-negativo",
        "side-invalido",
        "data-invalida",
    ],
)
def test_create_trade_rejects_invalid_payload(
    instrument: dict[str, Any], post_trade: PostTrade, overrides: dict[str, Any]
) -> None:
    assert post_trade(instrument["id"], **overrides).status_code == 400


def test_create_trade_rejects_unknown_instrument(post_trade: PostTrade) -> None:
    assert post_trade(999).status_code == 400


def test_create_trade_rejects_archived_instrument(
    app_client: TestClient[Litestar], instrument: dict[str, Any], post_trade: PostTrade
) -> None:
    assert app_client.delete(f"/api/v1/ativos/{instrument['id']}").status_code == 204
    assert post_trade(instrument["id"]).status_code == 400


def test_get_trade(app_client: TestClient[Litestar], trade: dict[str, Any]) -> None:
    response = app_client.get(f"/api/v1/boletas/{trade['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == trade["id"]


def test_get_unknown_trade_is_404(app_client: TestClient[Litestar]) -> None:
    assert app_client.get("/api/v1/boletas/999").status_code == 404


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("settle", "settle"),
        ("settle", "cancel"),
        ("cancel", "settle"),
        ("cancel", "cancel"),
    ],
)
def test_trade_leaves_pending_only_once(
    app_client: TestClient[Litestar], trade: dict[str, Any], first: str, second: str
) -> None:
    done = app_client.post(f"/api/v1/boletas/{trade['id']}/{first}")
    assert done.status_code == 200
    assert done.json()["status"] == {"settle": "SETTLED", "cancel": "CANCELLED"}[first]

    assert app_client.post(f"/api/v1/boletas/{trade['id']}/{second}").status_code == 409


@pytest.mark.parametrize("action", ["settle", "cancel"])
def test_transition_on_unknown_trade_is_404(app_client: TestClient[Litestar], action: str) -> None:
    assert app_client.post(f"/api/v1/boletas/999/{action}").status_code == 404


def test_list_trades_starts_empty(app_client: TestClient[Litestar]) -> None:
    response = app_client.get("/api/v1/boletas")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_list_trades_searches_by_fund_and_sorts_by_trade_date_desc(
    app_client: TestClient[Litestar], instrument: dict[str, Any], post_trade: PostTrade
) -> None:
    other_fund = "98765432000110"
    post_trade(instrument["id"], trade_date="2026-10-01")
    post_trade(instrument["id"], trade_date="2026-10-05")
    post_trade(instrument["id"], fund_cnpj=other_fund)

    everything = app_client.get("/api/v1/boletas").json()
    assert everything["total"] == 3
    dates = [item["trade_date"] for item in everything["items"]]
    assert dates == sorted(dates, reverse=True)

    filtered = app_client.get("/api/v1/boletas", params={"searchString": other_fund}).json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["fund_cnpj"] == other_fund
