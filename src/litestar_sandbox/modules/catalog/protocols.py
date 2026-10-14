from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from litestar_sandbox.modules.catalog.models import Product
    from litestar_sandbox.modules.catalog.schemas import ProductCreate, ProductUpdate


class ProductServiceProtocol(Protocol):
    async def get(self, item_id: int) -> Product: ...
    async def create(self, data: ProductCreate) -> Product: ...
    async def get_many_and_count(self, *filters: FilterTypes) -> tuple[Sequence[Product], int]: ...
    def to_schema(
        self, data: Sequence[Product], total: int, filters: Sequence[FilterTypes] | None = None
    ) -> OffsetPagination[Product]: ...
    async def update(self, data: ProductUpdate, item_id: int) -> Product: ...
