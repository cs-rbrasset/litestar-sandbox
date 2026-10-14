from typing import TYPE_CHECKING, TypeAlias

from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, get, post
from litestar.di import NamedDependency, Provide
from litestar.params import FromPath, SkipValidation, URLEncodedBody
from msgspec.structs import asdict

from litestar_sandbox.modules.catalog.models import Product
from litestar_sandbox.modules.catalog.protocols import ProductServiceProtocol
from litestar_sandbox.modules.catalog.schemas import ProductCreate
from litestar_sandbox.modules.catalog.services import ProductService

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.providers import FilterConfig

ProductServiceDep: TypeAlias = NamedDependency[SkipValidation[ProductServiceProtocol]]
ProductFilterDep: TypeAlias = NamedDependency[SkipValidation[list[FilterTypes]]]
product_filter_config: FilterConfig = {
    "pagination_type": "limit_offset",
    "search": "name",
    "sort_field": "created_at",
    "sort_order": "desc",
}


class ProductController(Controller):
    path = "/products"
    dependencies = {
        "product_service": Provide(create_service_provider(ProductService))
    } | create_filter_dependencies(product_filter_config)

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

    @get()
    async def list_products(
        self, product_service: ProductServiceDep, filters: ProductFilterDep
    ) -> OffsetPagination[Product]:
        items, total = await product_service.get_many_and_count(*filters)
        return product_service.to_schema(items, total, filters)
