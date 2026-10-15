import decimal
from typing import TYPE_CHECKING, Protocol

import msgspec
from advanced_alchemy.filters import CollectionFilter

from litestar_sandbox.core.deps import SessionDep
from litestar_sandbox.modules.instruments.services import InstrumentService

if TYPE_CHECKING:
    from collections.abc import Collection


class InstrumentSummary(msgspec.Struct, frozen=True):
    id: int
    name: str
    price: decimal.Decimal
    sku: str


class InstrumentPublicAPI(Protocol):
    async def get_instruments(self, ids: Collection[int]) -> dict[int, InstrumentSummary]: ...


class InstrumentPublicService:
    def __init__(self, instruments: InstrumentService) -> None:
        self._instruments = instruments

    async def get_instruments(self, ids: Collection[int]) -> dict[int, InstrumentSummary]:
        items, _ = await self._instruments.list_active(
            CollectionFilter(field_name="id", values=ids)
        )
        return {
            p.id: InstrumentSummary(price=p.price, sku=p.sku, name=p.name, id=p.id) for p in items
        }


async def provide_instrument_api(db_session: SessionDep) -> InstrumentPublicAPI:
    return InstrumentPublicService(InstrumentService(db_session))


__all__ = ("InstrumentPublicAPI", "InstrumentSummary", "provide_instrument_api")
