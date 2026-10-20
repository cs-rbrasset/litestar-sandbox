from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from litestar_sandbox.modules.positions.domain import Movement, Position, positions_at_date
from litestar_sandbox.modules.positions.models import PositionMovement
from litestar_sandbox.modules.positions.repositories import PositionMovementRepository
from litestar_sandbox.modules.trades.public import TradeSettled, TradeSide

if TYPE_CHECKING:
    import datetime


class PositionService(
    SQLAlchemyAsyncRepositoryService[PositionMovement, PositionMovementRepository]
):
    repository_type = PositionMovementRepository

    async def record_settlement(self, event: TradeSettled) -> PositionMovement:
        signed = event.quantity if event.side is TradeSide.BUY else -event.quantity
        return await self.create(
            {
                "trade_id": event.trade_id,
                "quantity": signed,
                "cetip_code": event.cetip_code,
                "instrument_id": event.instrument_id,
                "fund_cnpj": event.fund_cnpj,
                "movement_date": event.trade_date,
                "unit_price": event.unit_price,
            }
        )

    async def positions_at(self, fund_cnpj: str, reference_date: datetime.date) -> list[Position]:
        rows = await self.list(
            PositionMovement.fund_cnpj == fund_cnpj,
            PositionMovement.movement_date <= reference_date,
        )
        items = [
            Movement(
                instrument_id=r.instrument_id,
                cetip_code=r.cetip_code,
                movement_date=r.movement_date,
                quantity=r.quantity,
            )
            for r in rows
        ]
        return positions_at_date(items, reference_date)
