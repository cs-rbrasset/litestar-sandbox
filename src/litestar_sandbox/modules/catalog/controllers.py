from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get, post
from litestar.di import Provide
from msgspec.structs import asdict

from litestar_sandbox.modules.catalog.models import Product
from litestar_sandbox.modules.catalog.schemas import ProductCreate
from litestar_sandbox.modules.catalog.services import ProductService


class ProductController(Controller):
    path = "/products"
    dependencies = {"product_service": Provide(create_service_provider(ProductService))}


    @get("/{product_id:int}")
    async def get_product(self, product_service: ProductService, product_id: int) -> Product:
        return await product_service.get(product_id)

    @post()
    async def create_product(self, product_service: ProductService, data: ProductCreate) -> Product:
        return await product_service.create(asdict(data))
