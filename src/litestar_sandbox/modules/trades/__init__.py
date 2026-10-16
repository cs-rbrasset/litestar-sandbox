from litestar import Router

from litestar_sandbox.modules.trades.controllers import TradeController

trades_router = Router(path="/trades", route_handlers=[TradeController])
