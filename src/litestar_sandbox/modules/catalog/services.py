from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, is_dict

from litestar_sandbox.modules.catalog.models import Product
from litestar_sandbox.modules.catalog.repositories import ProductRepository


def _normalize_sku(data):
        if is_dict(data) and "sku" in data and data.get("sku") is not None:
            data["sku"] = data["sku"].strip().upper()
        elif isinstance(data, Product) and data.sku is not None:
            data.sku = data.sku.strip().upper()
        return data

class ProductService(SQLAlchemyAsyncRepositoryService[Product, ProductRepository]):
    repository_type = ProductRepository


    async def to_model_on_create(self, data):
        return await super().to_model_on_create(_normalize_sku(data))

    async def to_model_on_update(self, data):
        return await super().to_model_on_update(_normalize_sku(data))

