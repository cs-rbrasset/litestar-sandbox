from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from litestar_sandbox.modules.instruments.public import InstrumentPublicAPI
    from litestar_sandbox.modules.trades.models import Trade
    from litestar_sandbox.modules.trades.schemas import TradeCreate


class TradeServiceProtocol(Protocol):
    def to_schema(
        self, data: Sequence[Trade], total: int, filters: Sequence[FilterTypes] | None = None
    ) -> OffsetPagination[Trade]: ...

    async def register(self, data: TradeCreate, instruments_api: InstrumentPublicAPI) -> Trade: ...
    async def settle(self, item_id: int) -> Trade: ...
    async def cancel(self, item_id: int) -> Trade: ...
    async def get_trade(self, item_id: int) -> Trade: ...
    async def list_trades(self, *filters: FilterTypes) -> tuple[Sequence[Trade], int]: ...
