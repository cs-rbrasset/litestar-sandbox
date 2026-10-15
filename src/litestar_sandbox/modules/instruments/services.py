import datetime
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, is_dict, schema_dump

from litestar_sandbox.modules.instruments.models import Instrument
from litestar_sandbox.modules.instruments.repositories import InstrumentRepository

if TYPE_CHECKING:
    from collections.abc import Sequence

    from advanced_alchemy.filters import FilterTypes

    from litestar_sandbox.modules.instruments.schemas import InstrumentUpdate


def _normalize_cetip_code(data):
    if is_dict(data) and "cetip_code" in data and data.get("cetip_code") is not None:
        data["cetip_code"] = data["cetip_code"].strip().upper()
    return data


class InstrumentService(SQLAlchemyAsyncRepositoryService[Instrument, InstrumentRepository]):
    _active = Instrument.deleted_at.is_(None)

    repository_type = InstrumentRepository

    async def to_model_on_create(self, data):
        return await super().to_model_on_create(_normalize_cetip_code(schema_dump(data)))

    async def to_model_on_update(self, data):
        return await super().to_model_on_update(_normalize_cetip_code(schema_dump(data)))

    async def get_active(self, item_id: int) -> Instrument:
        return await self.get_one(Instrument.id == item_id, self._active)

    async def list_active(self, *filters: FilterTypes) -> tuple[Sequence[Instrument], int]:
        return await self.get_many_and_count(self._active, *filters)

    async def archive(self, item_id: int) -> Instrument:
        await self.get_active(item_id)  # 404 se não existir ou já arquivado
        now = datetime.datetime.now(datetime.UTC)
        return await self.update({"deleted_at": now}, item_id=item_id)

    async def update_active(self, data: InstrumentUpdate, item_id: int) -> Instrument:
        await self.get_active(item_id)  # 404 se não existir ou estiver arquivado
        return await self.update(data, item_id=item_id)
