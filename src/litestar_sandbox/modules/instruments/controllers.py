from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import FromPath, URLEncodedBody

from litestar_sandbox.core.deps import FilterDep
from litestar_sandbox.modules.instruments.deps import InstrumentServiceDep, instrument_filter_config
from litestar_sandbox.modules.instruments.models import Instrument
from litestar_sandbox.modules.instruments.schemas import InstrumentCreate, InstrumentUpdate
from litestar_sandbox.modules.instruments.services import InstrumentService


class InstrumentController(Controller):
    path = "/"
    dependencies = {"instrument_service": Provide(create_service_provider(InstrumentService))}

    @get("/{instrument_id:int}")
    async def get_instrument(
        self, instrument_service: InstrumentServiceDep, instrument_id: FromPath[int]
    ) -> Instrument:
        return await instrument_service.get_active(instrument_id)

    @post()
    async def create_instrument(
        self, instrument_service: InstrumentServiceDep, data: URLEncodedBody[InstrumentCreate]
    ) -> Instrument:
        return await instrument_service.create(data)

    @get(dependencies=create_filter_dependencies(instrument_filter_config))
    async def list_instruments(
        self, instrument_service: InstrumentServiceDep, filters: FilterDep
    ) -> OffsetPagination[Instrument]:
        items, total = await instrument_service.list_active(*filters)
        return instrument_service.to_schema(items, total, filters)

    @patch("/{instrument_id:int}")
    async def update_instrument(
        self,
        instrument_service: InstrumentServiceDep,
        instrument_id: FromPath[int],
        data: InstrumentUpdate,
    ) -> Instrument:
        return await instrument_service.update_active(data, instrument_id)

    @delete("/{instrument_id:int}")
    async def delete_instrument(
        self, instrument_service: InstrumentServiceDep, instrument_id: FromPath[int]
    ) -> None:
        await instrument_service.archive(instrument_id)
