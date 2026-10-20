from litestar import Router

from litestar_sandbox.modules.positions.controllers import PositionController
from litestar_sandbox.modules.positions.listeners import build_listeners

positions_router = Router(path="/positions", route_handlers=[PositionController])

__all__ = (
    "build_listeners",
    "positions_router",
)
