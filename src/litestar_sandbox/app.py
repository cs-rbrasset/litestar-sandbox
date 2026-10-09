from litestar import Litestar, get

from litestar_sandbox.core.database import sqlalchemy_plugin
from litestar_sandbox.modules.catalog import catalog_router


@get("/ping")
async def ping() -> str:
    return "pong"


app = Litestar(route_handlers=[ping, catalog_router], plugins=[sqlalchemy_plugin])
