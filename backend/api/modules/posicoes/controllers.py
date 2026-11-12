import datetime

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException, ServiceUnavailableException
from litestar.params import FromPath

from core.jobs import (
    EstadoJob,
    ExecucaoNaoEncontradaError,
    OrquestradorIndisponivelError,
    status,
)
from core.storage import armazenamento_padrao
from modules.posicoes.deps import PositionServiceDep
from modules.posicoes.domain import Position
from modules.posicoes.schemas import (
    PositionsReportHandle,
    PositionsReportPdfUrl,
    PositionsReportRequest,
    PositionsReportStatus,
)
from modules.posicoes.services import PositionService


class PositionController(Controller):
    path = "/posicoes"
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
    async def trigger_report(
        self, data: PositionsReportRequest, position_service: PositionServiceDep
    ) -> PositionsReportHandle:
        """Controller → service → `core.jobs.enfileirar`: nenhum dos três conhece o orquestrador.

        O id da execução volta na hora; o PDF fica pronto depois, no worker.
        """
        try:
            task_run_id = await position_service.request_report(
                data.fund_cnpj, data.reference_dates
            )
        except OrquestradorIndisponivelError as error:
            raise _orquestrador_indisponivel() from error
        return PositionsReportHandle(task_run_id=task_run_id)

    @get("/reports/{task_run_id:str}")
    async def get_report(self, task_run_id: FromPath[str]) -> PositionsReportStatus:
        execucao = await _estado(task_run_id)
        return PositionsReportStatus(task_run_id=task_run_id, state=execucao.estado)

    @get("/reports/{task_run_id:str}/pdf")
    async def get_report_pdf(self, task_run_id: FromPath[str]) -> PositionsReportPdfUrl:
        """O PDF mora no object storage; aqui só devolve uma signed URL curta pra ele."""
        execucao = await _estado(task_run_id)
        if not execucao.concluido:
            raise ClientException(status_code=409, detail="relatório ainda não terminou")
        url = await armazenamento_padrao().url_assinada(str(execucao.resultado))
        return PositionsReportPdfUrl(url=url)


async def _estado(task_run_id: str) -> EstadoJob:
    """Consulta de status é leitura pura: vai direto na porta, sem evento no meio."""
    try:
        return await status(task_run_id)
    except OrquestradorIndisponivelError as error:
        raise _orquestrador_indisponivel() from error
    except ExecucaoNaoEncontradaError as error:
        raise NotFoundException(detail=f"execução {task_run_id!r} não existe") from error


def _orquestrador_indisponivel() -> ServiceUnavailableException:
    return ServiceUnavailableException(detail="orquestrador de jobs indisponível")
