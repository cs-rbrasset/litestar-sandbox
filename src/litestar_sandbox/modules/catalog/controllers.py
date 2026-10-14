from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, get, post
from litestar.di import Provide
from litestar.params import FromPath, URLEncodedBody
from msgspec.structs import asdict

from litestar_sandbox.core.deps import FilterDep
from litestar_sandbox.modules.catalog.deps import ProductServiceDep, product_filter_config
from litestar_sandbox.modules.catalog.models import Product
from litestar_sandbox.modules.catalog.schemas import ProductCreate
from litestar_sandbox.modules.catalog.services import ProductService


class ProductController(Controller):
    path = "/products"
    dependencies = {"product_service": Provide(create_service_provider(ProductService))}

    @get("/{product_id:int}")
    async def get_product(
        self, product_service: ProductServiceDep, product_id: FromPath[int]
    ) -> Product:
        return await product_service.get(product_id)

    @post()
    async def create_product(
        self, product_service: ProductServiceDep, data: URLEncodedBody[ProductCreate]
    ) -> Product:
        return await product_service.create(asdict(data))

    @get(dependencies=create_filter_dependencies(product_filter_config))
    async def list_products(
        self, product_service: ProductServiceDep, filters: FilterDep
    ) -> OffsetPagination[Product]:
        items, total = await product_service.get_many_and_count(*filters)
        return product_service.to_schema(items, total, filters)
