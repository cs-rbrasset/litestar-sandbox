import logging
from typing import TYPE_CHECKING

import httpx
from advanced_alchemy.exceptions import DuplicateKeyError
from litestar.events import listener

from core.database import get_sqlalchemy_config
from core.identity import SYSTEM, use_identity
from modules.positions.events import (
    POSITIONS_REPORT_REQUESTED,
    PositionsReportRequested,
)
from modules.positions.services import PositionService
from modules.positions.tasks import recompute_positions_report
from modules.trades.public import TRADE_SETTLED, TradeSettled

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


@listener(POSITIONS_REPORT_REQUESTED)
async def on_positions_report_requested(event: PositionsReportRequested, app: Litestar) -> None:
    """Único lugar que conhece `recompute_positions_report`: o controller só publica o evento.

    `.delay()` é síncrono (cria o task run no Prefect e volta), mas quem publicou o evento está
    esperando no `future` — por isso resolve/rejeita ele aqui, em vez de deixar a exceção subir
    sem mais ninguém pra ouvir (o emissor do evento já seguiu em frente há muito tempo).
    `app` não é usado (não precisa de sessão): `publish()` sempre injeta esse kwarg.
    """
    if event.future.done():
        return
    try:
        future = recompute_positions_report.delay(
            fund_cnpj=event.fund_cnpj, reference_dates=event.reference_dates
        )
    except httpx.ConnectError as error:
        event.future.set_exception(error)
        return
    event.future.set_result(str(future.task_run_id))
