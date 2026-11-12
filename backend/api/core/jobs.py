"""Porta de jobs em background — o único lugar do app que importa `prefect`.

Módulo de negócio nunca importa `prefect`: declara o job com `@job(...)`, quebra o trabalho em
etapas com `@etapa(...)`, dispara com `enfileirar(...)` e consulta com `status(...)`. Trocar de
orquestrador é reescrever este arquivo, não os módulos. O contrato do import-linter "modules não
importa prefect" fiscaliza.

**Job é flow; etapa é task.** O job é a unidade que se dispara e se consulta (um id só); as
etapas são os passos com efeito colateral dentro dele, cada uma com o próprio retry. Uma falha
transitória numa etapa repete **só aquela etapa**, com o que as anteriores já produziram ainda em
memória — gravar o bruto falhou não faz baixar de novo do custodiante. Por isso o job em si não
tem retry: repetir o job inteiro refaria as etapas que já deram certo.

O job é publicado como **deployment** (`<nome do job>/padrao`) e disparado pelo nome:

  - dev: `worker.py` → `servir()` registra os deployments no server local e executa os runs no
    próprio processo;
  - produção: `implantar.py` publica no servidor Prefect da RBR via `rbr-prefect`; o run sobe
    num container que clona o repositório e carrega `fluxos.py` (ver lá por que existe).

Os dois caminhos usam o mesmo nome de deployment, então `enfileirar` não sabe onde está.

Não existe app Litestar no processo do job: job **não publica evento** — se precisa de outro
módulo, chama o `public.py` dele direto.
"""

import contextlib
import dataclasses
import functools
import importlib
import pkgutil
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

import httpx
from prefect import flow, get_client, serve, task
from prefect.deployments import arun_deployment
from prefect.deployments.runner import EntrypointType
from prefect.exceptions import ObjectNotFound
from prefect.flows import Flow
from prefect.runtime import flow_run

from core.database import create_sqlalchemy_config
from core.identity import SYSTEM, use_identity
from core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Coroutine

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from prefect.client.schemas.objects import State, TaskRun
    from prefect.tasks import Task
    from sqlalchemy.ext.asyncio import AsyncSession

#: nome do deployment de todo job, no server de dev e no de produção — é o que deixa
#: `enfileirar` chamar `<job>/padrao` sem saber em qual dos dois está.
NOME_DEPLOYMENT = "padrao"


class OrquestradorIndisponivelError(RuntimeError):
    """Não deu pra falar com o orquestrador (PREFECT_API_URL não respondeu)."""


class JobNaoPublicadoError(OrquestradorIndisponivelError):
    """O orquestrador respondeu, mas o deployment do job não existe nele.

    Em dev: o `worker.py` nunca subiu contra esse server. Em produção: faltou rodar o
    `implantar.py` depois de criar ou renomear o job. Para quem pede, dá no mesmo que o
    orquestrador fora do ar — por isso herda de `OrquestradorIndisponivelError`.
    """


class ExecucaoNaoEncontradaError(LookupError):
    """O id de execução não existe no orquestrador."""


@dataclasses.dataclass(frozen=True)
class EstadoJob:
    """O que o resto do sistema precisa saber de uma execução, sem vocabulário de Prefect."""

    id: str
    estado: str
    concluido: bool
    resultado: Any = None


def job(
    nome: str, *, nome_execucao: str | None = None
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Flow[..., Any]]:
    """Declara uma função async como job — a unidade que se dispara e se consulta.

    Sem retry de propósito: quem repete é cada `@etapa`. O resultado é persistido porque
    `status()` lê o retorno do job de outro processo (a API), não de quem o executou.

    Os parâmetros do job precisam ser serializáveis e de tipos simples: o orquestrador resolve
    as anotações num processo à parte, onde os tipos do módulo de origem podem não existir.
    """

    def decorador(fn: Callable[..., Coroutine[Any, Any, Any]]) -> Flow[..., Any]:
        @functools.wraps(fn)
        async def _execucao(*args: Any, **kwargs: Any) -> Any:
            # uma engine por execução do job (não por etapa nem por item processado): o
            # Prefect não tem hook de startup/shutdown pro processo, então o dispose mora aqui.
            # A ContextVar chega às etapas, que rodam no mesmo contexto do job.
            execucao = _Execucao()
            token = _execucao_atual.set(execucao)
            try:
                return await fn(*args, **kwargs)
            finally:
                _execucao_atual.reset(token)
                await execucao.encerrar()

        return flow(
            name=nome,
            flow_run_name=nome_execucao,
            retries=0,
            persist_result=True,
        )(_execucao)

    return decorador


def etapa(
    *,
    tentativas: int = 0,
    intervalo_s: int = 0,
    nao_repetir: tuple[type[BaseException], ...] = (),
) -> Callable[[Callable[..., Any]], Task[..., Any]]:
    """Declara um passo de um job, com retry próprio.

    `nao_repetir` recebe tipos de exceção que **não** devem disparar nova tentativa — erro de
    domínio (layout não reconhecido, validação) não melhora repetindo; falha de rede, sim.
    Recebe os tipos em vez de uma classe-base do `core` de propósito: o domínio não herda nada
    daqui, só aponta as próprias exceções.

    O resultado da etapa **não** é persistido: ele vive em memória até a próxima etapa do mesmo
    job. Persistir copiaria pro storage do orquestrador o que a etapa já guardou onde deve
    (o bruto do custodiante, por exemplo, mora em `brutos.py`, não aqui).
    """

    def decorador(fn: Callable[..., Any]) -> Task[..., Any]:
        return task(
            name=fn.__name__,
            retries=tentativas,
            retry_delay_seconds=intervalo_s or None,
            retry_condition_fn=_condicao_de_retry(nao_repetir) if nao_repetir else None,
            persist_result=False,
        )(fn)

    return decorador


def id_execucao_atual() -> str:
    """Id da execução corrente, lido de dentro do job — pra nomear o objeto que ele grava."""
    return str(flow_run.id)


async def enfileirar(job_declarado: Flow[..., Any], /, **parametros: Any) -> str:
    """Põe o job na fila e devolve o id da execução na hora — sem esperar o trabalho."""
    try:
        execucao = await arun_deployment(
            nome_do_deployment(job_declarado),
            parameters=parametros,
            timeout=0,  # não espera: devolve assim que o run é criado
            as_subflow=False,  # quem dispara é a API, não outro job
        )
    except httpx.ConnectError as erro:
        raise OrquestradorIndisponivelError(str(erro)) from erro
    except ObjectNotFound as erro:
        raise JobNaoPublicadoError(nome_do_deployment(job_declarado)) from erro
    return str(execucao.id)


async def status(id_execucao: str) -> EstadoJob:
    """Leitura pura: não passa por evento, não tem efeito colateral."""
    try:
        async with get_client() as client:
            execucao = await client.read_flow_run(id_execucao)
    except httpx.ConnectError as erro:
        raise OrquestradorIndisponivelError(str(erro)) from erro
    except ObjectNotFound as erro:
        raise ExecucaoNaoEncontradaError(id_execucao) from erro
    estado = execucao.state
    concluido = estado is not None and estado.is_completed()
    # dentro de código async: a versão sem "a" devolve uma coroutine, não o valor
    resultado = await estado.aresult(raise_on_failure=False) if concluido and estado else None
    return EstadoJob(
        id=id_execucao,
        estado=execucao.state_type.value if execucao.state_type else "UNKNOWN",
        concluido=concluido,
        resultado=resultado,
    )


@contextlib.asynccontextmanager
async def sessao_de_job() -> AsyncGenerator[AsyncSession]:
    """Sessão de banco pra código que roda no job, sem request por trás.

    Age como identidade de sistema de propósito (com `DB_ASSUME_IDENTITY`, transação sem
    identidade é recusada pelo Postgres) e faz commit à mão — o job é idempotente.
    Chamar isto várias vezes na mesma execução reusa a mesma engine.
    """
    execucao = _execucao_atual.get()
    propria = execucao is None
    if execucao is None:
        execucao = _Execucao()
    try:
        with use_identity(SYSTEM):
            async with execucao.config().get_session() as sessao:
                yield sessao
    finally:
        if propria:
            await execucao.encerrar()


#: mesmo contrato do `domain_packages` do autowire: o pacote é uma string, não um import —
#: `core` não pode importar `modules` (contrato do import-linter), e não precisa.
PACOTE_DE_MODULOS = "modules"


def descobrir(pacote: str = PACOTE_DE_MODULOS) -> list[Flow[..., Any]]:
    """Jobs declarados em `modules/*/tasks.py` — mesma ideia do autowire pros controllers."""
    raiz = importlib.import_module(pacote)

    achados: list[Flow[..., Any]] = []
    for info in pkgutil.iter_modules(raiz.__path__, f"{raiz.__name__}."):
        nome_modulo = f"{info.name}.tasks"
        try:
            modulo = importlib.import_module(nome_modulo)
        except ModuleNotFoundError as erro:
            if erro.name != nome_modulo:
                raise  # tasks.py existe mas tem import quebrado: não engole o erro
            continue
        achados.extend(
            valor
            for valor in vars(modulo).values()
            if isinstance(valor, Flow) and valor.fn.__module__ == modulo.__name__
        )
    return achados


def nome_do_deployment(job_declarado: Flow[..., Any]) -> str:
    return f"{job_declarado.name}/{NOME_DEPLOYMENT}"


def nome_no_entrypoint(job_declarado: Flow[..., Any]) -> str:
    """Nome do atributo que expõe o job no `fluxos.py` (o entrypoint de produção).

    Derivado do nome do job, não da função: duas `tasks.py` podem ter função com o mesmo nome,
    mas o nome do job é único (o deployment é chaveado por ele).
    """
    return job_declarado.name.replace("-", "_")


def servir(pacote: str = PACOTE_DE_MODULOS) -> None:
    """Dev: registra os deployments no server local e bloqueia executando os runs.

    Entrypoint por caminho de módulo (`modules.x.tasks.funcao`): o processo do runner já roda
    de `backend/api`, onde `core` e `modules` são importáveis. Produção não passa por aqui.
    """
    jobs = descobrir(pacote)
    if not jobs:
        msg = "nenhum job encontrado em modules/*/tasks.py"
        raise RuntimeError(msg)
    serve(
        *(
            j.to_deployment(name=NOME_DEPLOYMENT, entrypoint_type=EntrypointType.MODULE_PATH)
            for j in jobs
        )
    )


class _Execucao:
    """Recurso com estado compartilhado dentro de uma execução de job (hoje, a engine)."""

    def __init__(self) -> None:
        self._config: SQLAlchemyAsyncConfig | None = None

    def config(self) -> SQLAlchemyAsyncConfig:
        if self._config is None:
            self._config = create_sqlalchemy_config(DatabaseSettings.from_env())
        return self._config

    async def encerrar(self) -> None:
        if self._config is not None:
            await self._config.get_engine().dispose()
            self._config = None


_execucao_atual: ContextVar[_Execucao | None] = ContextVar("_execucao_atual", default=None)


def _condicao_de_retry(
    nao_repetir: tuple[type[BaseException], ...],
) -> Callable[[Task[..., Any], TaskRun, State[Any]], bool]:
    def pode_repetir(_etapa: Task[..., Any], _execucao: TaskRun, estado: State[Any]) -> bool:
        erro = estado.data if isinstance(estado.data, BaseException) else None
        # sem conseguir identificar a exceção, mantém o comportamento padrão (repetir)
        return not isinstance(erro, nao_repetir)

    return pode_repetir


__all__ = (
    "NOME_DEPLOYMENT",
    "EstadoJob",
    "ExecucaoNaoEncontradaError",
    "JobNaoPublicadoError",
    "OrquestradorIndisponivelError",
    "descobrir",
    "enfileirar",
    "etapa",
    "id_execucao_atual",
    "job",
    "nome_do_deployment",
    "nome_no_entrypoint",
    "servir",
    "sessao_de_job",
    "status",
)
