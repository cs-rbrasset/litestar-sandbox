import decimal
from typing import TYPE_CHECKING, Protocol

import msgspec
from advanced_alchemy.filters import CollectionFilter

from litestar_sandbox.core.deps import SessionDep
from litestar_sandbox.modules.catalog.services import ProductService

if TYPE_CHECKING:
    from collections.abc import Collection


class ProductSummary(msgspec.Struct, frozen=True):
    id: int
    name: str
    price: decimal.Decimal
    sku: str


class ProductPublicAPI(Protocol):
    async def get_products(self, ids: Collection[int]) -> dict[int, ProductSummary]: ...


class ProductPublicService:
    def __init__(self, products: ProductService) -> None:
        self._products = products

    async def get_products(self, ids: Collection[int]) -> dict[int, ProductSummary]:
        items, _ = await self._products.list_active(CollectionFilter(field_name="id", values=ids))
        return {p.id: ProductSummary(price=p.price, sku=p.sku, name=p.name, id=p.id) for p in items}


async def provide_product_api(db_session: SessionDep) -> ProductPublicAPI:
    return ProductPublicService(ProductService(db_session))


__all__ = ("ProductPublicAPI", "ProductSummary", "provide_product_api")
