from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from litestar_sandbox.modules.catalog.models import Product


class ProductServiceProtocol(Protocol):
    async def get(self, item_id: int) -> Product: ...
    async def create(self, data: dict[str, Any]) -> Product: ...
