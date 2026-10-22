from typing import Any

from litestar import Litestar, Router, get
from litestar.openapi import OpenAPIConfig
from litestar_autowire import AutowireConfig, AutowirePlugin

from litestar_sandbox.core.database import create_sqlalchemy_config, create_sqlalchemy_plugin
from litestar_sandbox.core.frontend import create_vite_plugin
from litestar_sandbox.core.settings import DatabaseSettings

API_PREFIX = "/api/v1"


class ApiRouter(Router):
    """Router em que o autowire registra os controllers descobertos.

    O prefixo fica num Router, e não em Litestar(path=...): o prefixo da app valeria também
    para a SPA, que iria parar em /api/v1/ em vez de /.
    """

    def __init__(self, path: str = "/", **kwargs: Any) -> None:
        super().__init__(path=API_PREFIX, **kwargs)


@get("/ping")
async def ping() -> str:
    return "pong"


def create_app(settings: DatabaseSettings | None = None) -> Litestar:
    if settings is None:
        settings = DatabaseSettings.from_env()
    config = create_sqlalchemy_config(settings)
    autowire = AutowirePlugin(
        AutowireConfig(domain_packages=["litestar_sandbox.modules"], router_class=ApiRouter)
    )
    return Litestar(
        route_handlers=[Router(API_PREFIX, route_handlers=[ping])],
        plugins=[create_sqlalchemy_plugin(config), autowire, create_vite_plugin(API_PREFIX)],
        openapi_config=OpenAPIConfig(
            title="litestar-sandbox", version="0.1.0", path=f"{API_PREFIX}/schema"
        ),
    )
