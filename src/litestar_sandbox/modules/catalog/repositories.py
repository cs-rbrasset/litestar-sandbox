from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from litestar_sandbox.modules.catalog.models import Product


class ProductRepository(SQLAlchemyAsyncRepository[Product]):
    model_type = Product

