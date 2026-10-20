from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from litestar_sandbox.modules.instruments.models import Instrument
    from litestar_sandbox.modules.instruments.schemas import (
        InstrumentCreate,
        InstrumentUpdate,
    )


class InstrumentServiceProtocol(Protocol):
    def to_schema(
        self, data: Sequence[Instrument], total: int, filters: Sequence[FilterTypes] | None = None
    ) -> OffsetPagination[Instrument]: ...

    async def create(self, data: InstrumentCreate) -> Instrument: ...
    async def list_active(self, *filters: FilterTypes) -> tuple[Sequence[Instrument], int]: ...
    async def update_active(self, data: InstrumentUpdate, item_id: int) -> Instrument: ...
    async def get_active(self, item_id: int) -> Instrument: ...
    async def archive(self, item_id: int) -> Instrument: ...
