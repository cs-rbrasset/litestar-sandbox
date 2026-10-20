from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import datetime

    from litestar_sandbox.modules.positions.domain import Position


class PositionServiceProtocol(Protocol):
    async def positions_at(
        self, fund_cnpj: str, reference_date: datetime.date
    ) -> list[Position]: ...
