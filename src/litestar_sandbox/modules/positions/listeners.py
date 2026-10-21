import logging
from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import DuplicateKeyError
from litestar.events import listener

from litestar_sandbox.core.database import get_sqlalchemy_config
from litestar_sandbox.modules.positions.services import PositionService
from litestar_sandbox.modules.trades.public import TRADE_SETTLED, TradeSettled

if TYPE_CHECKING:
    from litestar import Litestar


logger = logging.getLogger(__name__)


@listener(TRADE_SETTLED)
async def on_trade_settled(event: TradeSettled, app: Litestar) -> None:
    async with get_sqlalchemy_config(app).get_session() as session:
        service = PositionService(session=session)
        try:
            await service.record_settlement(event)
            await session.commit()
        except DuplicateKeyError:
            logger.info("trade %s is already stored", event.trade_id)
