from litestar import Litestar, get
from litestar_autowire import AutowireConfig, AutowirePlugin

from litestar_sandbox.core.database import create_sqlalchemy_config, create_sqlalchemy_plugin
from litestar_sandbox.core.settings import DatabaseSettings


@get("/ping")
async def ping() -> str:
    return "pong"


def create_app(settings: DatabaseSettings | None = None) -> Litestar:
    if settings is None:
        settings = DatabaseSettings.from_env()
    config = create_sqlalchemy_config(settings)
    plugin = create_sqlalchemy_plugin(config)
    autowire = AutowirePlugin(AutowireConfig(domain_packages=["litestar_sandbox.modules"]))
    return Litestar(
        path="/api/v1",
        route_handlers=[ping],
        plugins=[plugin, autowire],
    )
