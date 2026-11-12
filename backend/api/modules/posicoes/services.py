from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from core.jobs import enfileirar
from modules.boletas.public import TradeSettled, TradeSide
from modules.posicoes.domain import Movement, Position, positions_at_date
from modules.posicoes.models import PositionMovement
from modules.posicoes.repositories import PositionMovementRepository

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

    async def request_report(
        self, fund_cnpj: str, reference_dates: list[datetime.date]
    ) -> str:
        """Enfileira o job e devolve o id da execução na hora — o controller não espera o PDF.

        O import do job é adiado de propósito: `tasks.py` importa este service pra ler posição
        dentro da execução, então um import no topo daqui fecharia um ciclo.
        """
        from modules.posicoes.tasks import recompute_positions_report  # noqa: PLC0415

        return await enfileirar(
            recompute_positions_report, fund_cnpj=fund_cnpj, reference_dates=reference_dates
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
