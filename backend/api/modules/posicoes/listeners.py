import logging
from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import DuplicateKeyError
from litestar.events import listener

from core.database import get_sqlalchemy_config
from core.identity import SYSTEM, use_identity
from modules.boletas.public import TRADE_SETTLED, TradeSettled
from modules.posicoes.services import PositionService

if TYPE_CHECKING:
    from litestar import Litestar


logger = logging.getLogger(__name__)


@listener(TRADE_SETTLED)
async def on_trade_settled(event: TradeSettled, app: Litestar) -> None:
    # o listener roda fora do request, sem a identidade de quem liquidou: age como
    # identidade de sistema, declarada de propósito (sem ela, o Postgres recusa a transação)
    with use_identity(SYSTEM):
        async with get_sqlalchemy_config(app).get_session() as session:
            service = PositionService(session=session)
            try:
                await service.record_settlement(event)
                await session.commit()
            except DuplicateKeyError:
                logger.info("trade %s is already stored", event.trade_id)
