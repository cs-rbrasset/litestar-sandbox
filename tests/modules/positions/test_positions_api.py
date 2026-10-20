import time
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx
    from litestar import Litestar
    from litestar.testing import TestClient

    CreateInstrument = Callable[..., dict[str, Any]]
    PostTrade = Callable[..., httpx.Response]

FUND_CNPJ = "12345678000190"


def get_positions(client: TestClient[Litestar], reference_date: str) -> list[dict[str, Any]]:
    response = client.get(
        "/api/v1/positions", params={"fund_cnpj": FUND_CNPJ, "reference_date": reference_date}
    )
    assert response.status_code == 200, response.text
    return response.json()


def wait_for_positions(
    client: TestClient[Litestar], reference_date: str, expected: int
) -> list[dict[str, Any]]:
    """O listener do TradeSettled roda em segundo plano: espera as movimentações aparecerem."""
    deadline = time.monotonic() + 5
    while True:
        positions = get_positions(client, reference_date)
        if sum(abs(p["quantity"]) for p in positions) == expected or time.monotonic() > deadline:
            return positions
        time.sleep(0.05)


@pytest.fixture
def settle(app_client: TestClient[Litestar], post_trade: PostTrade) -> Callable[..., dict]:
    def _settle(instrument_id: int, **overrides: Any) -> dict[str, Any]:
        trade = post_trade(instrument_id, **overrides).json()
        response = app_client.post(f"/api/v1/trades/{trade['id']}/settle")
        assert response.status_code == 200, response.text
        return trade

    return _settle


def test_no_positions_for_unknown_fund(app_client: TestClient[Litestar]) -> None:
    assert get_positions(app_client, "2026-10-20") == []


def test_reference_date_is_required(app_client: TestClient[Litestar]) -> None:
    response = app_client.get("/api/v1/positions", params={"fund_cnpj": FUND_CNPJ})
    assert response.status_code == 400


def test_settled_buy_becomes_position(
    app_client: TestClient[Litestar], create_instrument: CreateInstrument, settle: Callable
) -> None:
    instrument = create_instrument(cetip_code="ABCD4")
    settle(instrument["id"], quantity=100, trade_date="2026-10-01")

    positions = wait_for_positions(app_client, "2026-10-20", expected=100)

    assert positions == [{"instrument_id": instrument["id"], "cetip_code": "ABCD4", "quantity": 100}]


def test_sell_reduces_position(
    app_client: TestClient[Litestar], create_instrument: CreateInstrument, settle: Callable
) -> None:
    instrument = create_instrument(cetip_code="ABCD4")
    settle(instrument["id"], side="BUY", quantity=100, trade_date="2026-10-01")
    settle(instrument["id"], side="SELL", quantity=30, trade_date="2026-10-02")

    positions = wait_for_positions(app_client, "2026-10-20", expected=70)

    assert [p["quantity"] for p in positions] == [70]


def test_position_respects_reference_date(
    app_client: TestClient[Litestar], create_instrument: CreateInstrument, settle: Callable
) -> None:
    instrument = create_instrument(cetip_code="ABCD4")
    settle(instrument["id"], quantity=100, trade_date="2026-10-05")
    wait_for_positions(app_client, "2026-10-20", expected=100)

    assert get_positions(app_client, "2026-10-04") == []
    assert [p["quantity"] for p in get_positions(app_client, "2026-10-05")] == [100]


def test_pending_and_cancelled_trades_do_not_move_position(
    app_client: TestClient[Litestar],
    create_instrument: CreateInstrument,
    post_trade: PostTrade,
    settle: Callable,
) -> None:
    instrument = create_instrument(cetip_code="ABCD4")
    post_trade(instrument["id"], quantity=10)  # fica PENDING
    cancelled = post_trade(instrument["id"], quantity=20).json()
    app_client.post(f"/api/v1/trades/{cancelled['id']}/cancel")
    settle(instrument["id"], quantity=100)  # a única liquidada

    positions = wait_for_positions(app_client, "2026-10-20", expected=100)

    assert [p["quantity"] for p in positions] == [100]
