import datetime

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get
from litestar.di import Provide

from litestar_sandbox.modules.positions.deps import PositionServiceDep
from litestar_sandbox.modules.positions.domain import Position
from litestar_sandbox.modules.positions.services import PositionService


class PositionController(Controller):
    path = "/"
    dependencies = {"position_service": Provide(create_service_provider(PositionService))}

    @get()
    async def get_positions(
        self,
        position_service: PositionServiceDep,
        fund_cnpj: str,
        reference_date: datetime.date,
    ) -> list[Position]:
        return await position_service.positions_at(fund_cnpj, reference_date)
