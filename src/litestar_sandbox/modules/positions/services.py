from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from litestar_sandbox.modules.positions.models import PositionMovement
from litestar_sandbox.modules.positions.repositories import PositionMovementRepository
from litestar_sandbox.modules.trades.public import TradeSettled, TradeSide


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
