from litestar import Router

from litestar_sandbox.modules.catalog.controllers import ProductController

catalog_router = Router(path="/catalog", route_handlers=[ProductController])
