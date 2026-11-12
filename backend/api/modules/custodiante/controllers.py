from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException, ServiceUnavailableException
from litestar.params import FromPath

from core.jobs import ExecucaoNaoEncontradaError, OrquestradorIndisponivelError
from modules.custodiante.deps import ImportacaoServiceDep, provide_importacao_service
from modules.custodiante.registro import CustodianteDesconhecidoError
from modules.custodiante.schemas import (
    ExecucaoHandle,
    ExecucaoStatus,
    ImportacaoRequest,
    ReprocessamentoRequest,
)


class ImportacaoController(Controller):
    path = "/custodiantes"
    dependencies = {"importacao_service": Provide(provide_importacao_service)}

    @post("/importacoes", status_code=202)
    async def solicitar(
        self, data: ImportacaoRequest, importacao_service: ImportacaoServiceDep
    ) -> ExecucaoHandle:
        """Controller → service → `core.jobs.enfileirar`. Nenhum deles conhece o orquestrador."""
        try:
            id_execucao = await importacao_service.solicitar_importacao(
                data.codigo, data.documento, data.fundo_cnpj, data.data
            )
        except CustodianteDesconhecidoError as erro:
            raise ClientException(detail=f"custodiante {data.codigo} não registrado") from erro
        except OrquestradorIndisponivelError as erro:
            raise _indisponivel() from erro
        return ExecucaoHandle(id_execucao=id_execucao)

    @post("/reprocessamentos", status_code=202)
    async def reprocessar(
        self, data: ReprocessamentoRequest, importacao_service: ImportacaoServiceDep
    ) -> ExecucaoHandle:
        """Relê um bruto já guardado — não chama o custodiante de novo."""
        try:
            id_execucao = await importacao_service.solicitar_reprocessamento(
                data.documento, data.prefixo, forcar=data.forcar
            )
        except OrquestradorIndisponivelError as erro:
            raise _indisponivel() from erro
        return ExecucaoHandle(id_execucao=id_execucao)

    @get("/importacoes/{id_execucao:str}")
    async def consultar(
        self, id_execucao: FromPath[str], importacao_service: ImportacaoServiceDep
    ) -> ExecucaoStatus:
        """Leitura pura: vai direto na porta de jobs, sem evento no meio."""
        try:
            execucao = await importacao_service.consultar(id_execucao)
        except OrquestradorIndisponivelError as erro:
            raise _indisponivel() from erro
        except ExecucaoNaoEncontradaError as erro:
            raise NotFoundException(detail=f"execução {id_execucao!r} não existe") from erro
        return ExecucaoStatus(
            id_execucao=execucao.id,
            estado=execucao.estado,
            concluido=execucao.concluido,
            referencia_origem=str(execucao.resultado) if execucao.resultado else None,
        )


def _indisponivel() -> ServiceUnavailableException:
    return ServiceUnavailableException(detail="orquestrador de jobs indisponível")
