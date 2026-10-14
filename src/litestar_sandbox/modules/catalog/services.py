import datetime
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, is_dict, schema_dump

from litestar_sandbox.modules.catalog.models import Product
from litestar_sandbox.modules.catalog.repositories import ProductRepository

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes

    from litestar_sandbox.modules.catalog.schemas import ProductUpdate


def _normalize_sku(data):
    if is_dict(data) and "sku" in data and data.get("sku") is not None:
        data["sku"] = data["sku"].strip().upper()
    return data


class ProductService(SQLAlchemyAsyncRepositoryService[Product, ProductRepository]):
    _active = Product.deleted_at.is_(None)

    repository_type = ProductRepository

    async def to_model_on_create(self, data):
        return await super().to_model_on_create(_normalize_sku(schema_dump(data)))

    async def to_model_on_update(self, data):
        return await super().to_model_on_update(_normalize_sku(schema_dump(data)))

    async def get_active(self, item_id: int) -> Product:
        return await self.get_one(Product.id == item_id, self._active)

    async def list_active(self, *filters: FilterTypes) -> tuple[Sequence[Product], int]:
        return await self.get_many_and_count(self._active, *filters)

    async def archive(self, item_id: int) -> Product:
        await self.get_active(item_id)  # 404 se não existir ou já arquivado
        now = datetime.datetime.now(datetime.UTC)
        return await self.update({"deleted_at": now}, item_id=item_id)

    async def update_active(self, data: ProductUpdate, item_id: int) -> Product:
        await self.get_active(item_id)  # 404 se não existir ou estiver arquivado
        return await self.update(data, item_id=item_id)
