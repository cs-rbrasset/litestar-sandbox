import os
from typing import Any

from litestar import Litestar, Router, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme
from litestar_autowire import AutowireConfig, AutowirePlugin

from litestar_sandbox.core.auth import AuthMiddleware, TokenVerifier, build_verifier
from litestar_sandbox.core.database import create_sqlalchemy_config, create_sqlalchemy_plugin
from litestar_sandbox.core.settings import DatabaseSettings
from litestar_sandbox.core.vite import create_vite_plugin

API_PREFIX = "/api/v1"


class ApiRouter(Router):
    """Router em que o autowire registra os controllers descobertos."""

    def __init__(self, path: str = "/", **kwargs: Any) -> None:
        super().__init__(path=API_PREFIX, **kwargs)


@get("/ping")
async def ping() -> str:
    return "pong"


def _cors_config() -> CORSConfig:
    """API pura, sem front same-origin: CORS_ALLOWED_ORIGINS="a,b" pra trocar o default.

    web-svelte-kit (porta 5173) é processo próprio, cross-origin de verdade.
    """
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return CORSConfig(allow_origins=origins, allow_headers=["Authorization", "Content-Type"])


def create_app(
    settings: DatabaseSettings | None = None, verifier: TokenVerifier | None = None
) -> Litestar:
    if settings is None:
        settings = DatabaseSettings.from_env()
    if verifier is None:
        verifier = build_verifier(settings.database_url)
    config = create_sqlalchemy_config(settings)
    autowire = AutowirePlugin(
        AutowireConfig(domain_packages=["litestar_sandbox.modules"], router_class=ApiRouter)
    )
    return Litestar(
        route_handlers=[Router(API_PREFIX, route_handlers=[ping])],
        plugins=[create_sqlalchemy_plugin(config), autowire, create_vite_plugin()],
        middleware=[AuthMiddleware(verifier, API_PREFIX)],
        cors_config=_cors_config(),
        openapi_config=OpenAPIConfig(
            title="litestar-sandbox",
            version="0.1.0",
            path=f"{API_PREFIX}/schema",
            components=Components(
                security_schemes={"BearerToken": SecurityScheme(type="http", scheme="bearer")}
            ),
            security=[{"BearerToken": []}],
        ),
    )
