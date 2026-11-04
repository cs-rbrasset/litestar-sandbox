from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, schema_dump
from litestar.exceptions import ClientException, ValidationException

from modules.boletas.enums import TradeStatus
from modules.boletas.models import Trade
from modules.boletas.repositories import TradeRepository

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes

    from modules.ativos.public import InstrumentPublicAPI
    from modules.boletas.schemas import TradeCreate


class TradeService(SQLAlchemyAsyncRepositoryService[Trade, TradeRepository]):
    repository_type = TradeRepository

    async def register(self, data: TradeCreate, instruments_api: InstrumentPublicAPI) -> Trade:
        found = await instruments_api.get_instruments([data.instrument_id])
        if data.instrument_id not in found:
            raise ValidationException(
                detail=f"instrument {data.instrument_id} not found or archived"
            )
        return await self.create(
            schema_dump(data) | {"cetip_code": found[data.instrument_id].cetip_code}
        )

    async def _transition(self, item_id: int, to: TradeStatus) -> Trade:
        trade = await self.repository.get(item_id=item_id, with_for_update=True)
        if trade.status is not TradeStatus.PENDING:
            raise ClientException(status_code=409, detail=f"trade {item_id} is {trade.status}")
        return await self.update({"status": to}, item_id=item_id)

    async def settle(self, item_id: int) -> Trade:
        return await self._transition(item_id=item_id, to=TradeStatus.SETTLED)

    async def cancel(self, item_id: int) -> Trade:
        return await self._transition(item_id=item_id, to=TradeStatus.CANCELLED)

    async def list_trades(self, *filters: FilterTypes) -> tuple[Sequence[Trade], int]:
        return await self.get_many_and_count(*filters)

    async def get_trade(self, item_id: int) -> Trade:
        return await self.get(item_id=item_id)
