from litestar import Litestar, get

from litestar_sandbox.core.database import create_sqlalchemy_config, create_sqlalchemy_plugin
from litestar_sandbox.core.settings import DatabaseSettings
from litestar_sandbox.modules.instruments import instruments_router
from litestar_sandbox.modules.positions import build_listeners, positions_router
from litestar_sandbox.modules.trades import trades_router


@get("/ping")
async def ping() -> str:
    return "pong"


def create_app(settings: DatabaseSettings | None = None) -> Litestar:
    if settings is None:
        settings = DatabaseSettings.from_env()
    config = create_sqlalchemy_config(settings)
    plugin = create_sqlalchemy_plugin(config)
    return Litestar(
        path="/api/v1",
        route_handlers=[ping, instruments_router, trades_router, positions_router],
        plugins=[plugin],
        listeners=build_listeners(config),
    )
