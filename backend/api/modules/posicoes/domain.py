import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    from collections.abc import Iterable


@dataclasses.dataclass(frozen=True)
class Movement:
    instrument_id: int
    cetip_code: str
    movement_date: datetime.date
    quantity: int


@dataclasses.dataclass(frozen=True)
class Position:
    instrument_id: int
    cetip_code: str
    quantity: int


def positions_at_date(
    movements: Iterable[Movement], reference_date: datetime.date
) -> list[Position]:
    totals: dict[int, int] = {}
    codes: dict[int, str] = {}
    for movement in movements:
        if movement.movement_date > reference_date:
            continue
        totals[movement.instrument_id] = totals.get(movement.instrument_id, 0) + movement.quantity
        codes[movement.instrument_id] = movement.cetip_code
    return sorted(
        [
            Position(instrument_id=i, cetip_code=codes[i], quantity=n)
            for i, n in totals.items()
            if n != 0
        ],
        key=lambda s: s.cetip_code,
    )
