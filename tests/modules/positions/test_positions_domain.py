import datetime

from litestar_sandbox.modules.positions.domain import Movement, Position, positions_at_date

D1 = datetime.date(2026, 10, 1)
D2 = datetime.date(2026, 10, 2)
D3 = datetime.date(2026, 10, 3)


def movement(instrument_id: int, day: datetime.date, quantity: int, code: str = "") -> Movement:
    return Movement(
        instrument_id=instrument_id,
        cetip_code=code or f"ATV{instrument_id}",
        movement_date=day,
        quantity=quantity,
    )


def test_no_movements_no_positions() -> None:
    assert positions_at_date([], D1) == []


def test_movements_after_reference_date_are_ignored() -> None:
    assert positions_at_date([movement(1, D2, 10)], D1) == []


def test_movement_on_reference_date_counts() -> None:
    assert positions_at_date([movement(1, D1, 10)], D1) == [Position(1, "ATV1", 10)]


def test_buys_and_sells_add_up_per_instrument() -> None:
    movements = [movement(1, D1, 100), movement(1, D2, -30), movement(2, D1, 5)]
    assert positions_at_date(movements, D3) == [Position(1, "ATV1", 70), Position(2, "ATV2", 5)]


def test_zeroed_position_is_omitted() -> None:
    assert positions_at_date([movement(1, D1, 50), movement(1, D2, -50)], D3) == []


def test_negative_position_is_kept() -> None:
    assert positions_at_date([movement(1, D1, -20)], D1) == [Position(1, "ATV1", -20)]


def test_positions_are_sorted_by_cetip_code() -> None:
    movements = [
        movement(1, D1, 1, "ZZZZ4"),
        movement(2, D1, 1, "AAAA4"),
        movement(3, D1, 1, "MMMM4"),
    ]
    codes = [p.cetip_code for p in positions_at_date(movements, D1)]
    assert codes == ["AAAA4", "MMMM4", "ZZZZ4"]
