import logging
from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import DuplicateKeyError
from litestar.events import EventListener, listener

from litestar_sandbox.modules.positions.services import PositionService
from litestar_sandbox.modules.trades.public import TRADE_SETTLED, TradeSettled

if TYPE_CHECKING:
    from advanced_alchemy.config import SQLAlchemyAsyncConfig


logger = logging.getLogger(__name__)


def build_listeners(config: SQLAlchemyAsyncConfig) -> list[EventListener]:
    @listener(TRADE_SETTLED)
    async def on_trade_settled(event: TradeSettled) -> None:
        async with config.get_session() as session:
            service = PositionService(session=session)
            try:
                await service.record_settlement(event)
                await session.commit()
            except DuplicateKeyError:
                logger.info("trade %s is already stored", event.trade_id)

    return [on_trade_settled]
