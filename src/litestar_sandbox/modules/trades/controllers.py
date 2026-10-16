from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, get, post
from litestar.di import Provide
from litestar.params import FromPath

from litestar_sandbox.core.deps import FilterDep
from litestar_sandbox.modules.instruments.public import provide_instrument_api
from litestar_sandbox.modules.trades.deps import (
    InstrumentPublicAPIDep,
    TradeServiceDep,
    trade_filter_config,
)
from litestar_sandbox.modules.trades.models import Trade
from litestar_sandbox.modules.trades.schemas import TradeCreate
from litestar_sandbox.modules.trades.services import TradeService


class TradeController(Controller):
    path = "/"
    dependencies = {"trade_service": Provide(create_service_provider(TradeService))}

    @post(dependencies={"instruments_api": Provide(provide_instrument_api)})
    async def create_trade(
        self,
        trade_service: TradeServiceDep,
        data: TradeCreate,
        instruments_api: InstrumentPublicAPIDep,
    ) -> Trade:
        return await trade_service.register(data, instruments_api)

    @get(dependencies=create_filter_dependencies(trade_filter_config))
    async def list_trades(
        self, trade_service: TradeServiceDep, filters: FilterDep
    ) -> OffsetPagination[Trade]:
        items, total = await trade_service.list_trades(*filters)
        return trade_service.to_schema(items, total, filters)

    @get("/{trade_id:int}")
    async def get_trade(self, trade_service: TradeServiceDep, trade_id: FromPath[int]) -> Trade:
        return await trade_service.get_trade(trade_id)

    @post("/{trade_id:int}/settle", status_code=200)
    async def settle_trade(self, trade_service: TradeServiceDep, trade_id: FromPath[int]) -> Trade:
        return await trade_service.settle(trade_id)

    @post("/{trade_id:int}/cancel", status_code=200)
    async def cancel_trade(self, trade_service: TradeServiceDep, trade_id: FromPath[int]) -> Trade:
        return await trade_service.cancel(trade_id)
