import datetime

import httpx
from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException, ServiceUnavailableException
from litestar.params import FromPath
from prefect import get_client
from prefect.exceptions import ObjectNotFound

from litestar_sandbox.core.settings import SupabaseSettings
from litestar_sandbox.core.storage import create_signed_url
from litestar_sandbox.modules.positions.deps import PositionServiceDep
from litestar_sandbox.modules.positions.domain import Position
from litestar_sandbox.modules.positions.schemas import (
    PositionsReportHandle,
    PositionsReportPdfUrl,
    PositionsReportRequest,
    PositionsReportStatus,
)
from litestar_sandbox.modules.positions.services import PositionService
from litestar_sandbox.modules.positions.tasks import recompute_positions_report


class PositionController(Controller):
    path = "/positions"
    dependencies = {"position_service": Provide(create_service_provider(PositionService))}

    @get()
    async def get_positions(
        self,
        position_service: PositionServiceDep,
        fund_cnpj: str,
        reference_date: datetime.date,
    ) -> list[Position]:
        return await position_service.positions_at(fund_cnpj, reference_date)

    @post("/reports", status_code=202)
    async def trigger_report(self, data: PositionsReportRequest) -> PositionsReportHandle:
        """Dispara a background task do Prefect (.delay): sem deployment, sem flow."""
        try:
            future = recompute_positions_report.delay(
                fund_cnpj=data.fund_cnpj, reference_dates=data.reference_dates
            )
        except httpx.ConnectError as error:
            raise _prefect_unavailable() from error
        return PositionsReportHandle(task_run_id=str(future.task_run_id))

    @get("/reports/{task_run_id:str}")
    async def get_report(self, task_run_id: FromPath[str]) -> PositionsReportStatus:
        try:
            async with get_client() as client:
                task_run = await client.read_task_run(task_run_id)
        except httpx.ConnectError as error:
            raise _prefect_unavailable() from error
        except ObjectNotFound as error:
            raise NotFoundException(detail=f"task_run {task_run_id!r} não existe") from error
        state = task_run.state_type.value if task_run.state_type else "UNKNOWN"
        return PositionsReportStatus(task_run_id=task_run_id, state=state)

    @get("/reports/{task_run_id:str}/pdf")
    async def get_report_pdf(self, task_run_id: FromPath[str]) -> PositionsReportPdfUrl:
        """O PDF mora no Supabase Storage; aqui só devolve uma signed URL curta pra ele."""
        try:
            async with get_client() as client:
                task_run = await client.read_task_run(task_run_id)
        except httpx.ConnectError as error:
            raise _prefect_unavailable() from error
        except ObjectNotFound as error:
            raise NotFoundException(detail=f"task_run {task_run_id!r} não existe") from error
        if task_run.state is None or not task_run.state.is_completed():
            raise ClientException(status_code=409, detail="relatório ainda não terminou")
        # dentro de um handler async: a versão sem "a" devolve uma coroutine e não o valor
        path = await task_run.state.aresult(raise_on_failure=False)
        url = await create_signed_url(SupabaseSettings.from_env(), path)
        return PositionsReportPdfUrl(url=url)


def _prefect_unavailable() -> ServiceUnavailableException:
    return ServiceUnavailableException(detail="Prefect indisponível: PREFECT_API_URL não respondeu")
