from litestar import Litestar, get

from litestar_sandbox.core.database import create_sqlalchemy_plugin
from litestar_sandbox.core.settings import DatabaseSettings
from litestar_sandbox.modules.catalog import catalog_router


@get("/ping")
async def ping() -> str:
    return "pong"


def create_app(settings: DatabaseSettings | None = None) -> Litestar:
    if settings is None:
        settings = DatabaseSettings.from_env()
    plugin = create_sqlalchemy_plugin(settings)
    return Litestar(route_handlers=[ping, catalog_router], plugins=[plugin])
