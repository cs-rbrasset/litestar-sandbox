"""Porta de jobs em background — o único lugar do backend que importa `prefect`.

Módulo de negócio nunca importa `prefect`: declara o job com `@job(...)`, dispara com
`enfileirar(...)` e consulta com `status(...)`. Trocar de orquestrador é reescrever este
arquivo, não os módulos. O contrato do import-linter "modules não importa prefect" fiscaliza.

Isso substitui o padrão antigo (controller publica evento + `asyncio.Future`, listener chama
`.delay()`): o evento existia só pra esconder o Prefect do controller, e a porta faz isso
direto, sem o future. Evento continua sendo o mecanismo entre **módulos** (`core/events.py`).

O worker (`backend/api/worker.py`) chama `servir()`, que descobre os jobs declarados em
`modules/*/tasks.py`. Não existe app Litestar no processo do worker: job **não publica
evento** — se um job precisa de outro módulo, chama o `public.py` dele direto.

Pré-requisitos (fora deste processo):
  - server: prefect server start   (ou PREFECT_API_URL apontando pra um já no ar)
  - worker: uv run --env-file ../../.env python worker.py
            (--env-file é obrigatório: ao contrário de "litestar run", um "python" solto
            não carrega o .env sozinho)
"""

import asyncio
import contextlib
import dataclasses
import functools
import importlib
import pkgutil
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

import httpx
from prefect import get_client, task
from prefect.exceptions import ObjectNotFound
from prefect.runtime import task_run
from prefect.task_worker import serve
from prefect.tasks import Task

from core.database import create_sqlalchemy_config
from core.identity import SYSTEM, use_identity
from core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Coroutine

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from prefect.client.schemas.objects import State, TaskRun
    from sqlalchemy.ext.asyncio import AsyncSession


class OrquestradorIndisponivelError(RuntimeError):
    """Não deu pra falar com o orquestrador (PREFECT_API_URL não respondeu)."""


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
    nome: str,
    *,
    nome_execucao: str | None = None,
    tentativas: int = 0,
    intervalo_s: int = 0,
    nao_repetir: tuple[type[BaseException], ...] = (),
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Task[..., Any]]:
    """Declara uma função async como job em background.

    `nao_repetir` recebe tipos de exceção que **não** devem disparar nova tentativa — erro de
    domínio (layout não reconhecido, validação) não melhora repetindo; falha de coleta, sim.
    Recebe os tipos em vez de uma classe-base do `core` de propósito: o domínio não herda nada
    daqui, só aponta as próprias exceções.

    Os parâmetros do job precisam ser serializáveis e de tipos simples: o orquestrador resolve
    as anotações num processo à parte, onde os tipos do módulo de origem podem não existir.
    """

    def decorador(fn: Callable[..., Coroutine[Any, Any, Any]]) -> Task[..., Any]:
        @functools.wraps(fn)
        async def _execucao(*args: Any, **kwargs: Any) -> Any:
            # uma engine por execução do job (não por item processado): o Prefect não tem hook
            # de startup/shutdown pro worker, então o dispose mora aqui.
            execucao = _Execucao()
            token = _execucao_atual.set(execucao)
            try:
                return await fn(*args, **kwargs)
            finally:
                _execucao_atual.reset(token)
                await execucao.encerrar()

        return task(
            name=nome,
            task_run_name=nome_execucao,
            retries=tentativas,
            retry_delay_seconds=intervalo_s or None,
            retry_condition_fn=_condicao_de_retry(nao_repetir) if nao_repetir else None,
            persist_result=True,
        )(_execucao)

    return decorador


def id_execucao_atual() -> str:
    """Id da execução corrente, lido de dentro do job — pra nomear o objeto que ele grava."""
    return str(task_run.id)


async def enfileirar(job_declarado: Task[..., Any], /, **parametros: Any) -> str:
    """Põe o job na fila e devolve o id da execução na hora — sem esperar o trabalho."""
    try:
        # .delay() é síncrono e faz HTTP: fora da thread do loop pra não travar a API
        futuro = await asyncio.to_thread(job_declarado.delay, **parametros)
    except httpx.ConnectError as erro:
        raise OrquestradorIndisponivelError(str(erro)) from erro
    return str(futuro.task_run_id)


async def status(id_execucao: str) -> EstadoJob:
    """Leitura pura: não passa por evento, não tem efeito colateral."""
    try:
        async with get_client() as client:
            execucao = await client.read_task_run(id_execucao)
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
    """Sessão de banco pra código que roda no worker, sem request por trás.

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


def descobrir(pacote: str = PACOTE_DE_MODULOS) -> list[Task[..., Any]]:
    """Jobs declarados em `modules/*/tasks.py` — mesma ideia do autowire pros controllers."""
    raiz = importlib.import_module(pacote)

    achados: list[Task[..., Any]] = []
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
            if isinstance(valor, Task) and valor.fn.__module__ == modulo.__name__
        )
    return achados


def servir(pacote: str = PACOTE_DE_MODULOS) -> None:
    """Bloqueia servindo todos os jobs descobertos (o processo do worker vive aqui)."""
    jobs = descobrir(pacote)
    if not jobs:
        msg = "nenhum job encontrado em modules/*/tasks.py"
        raise RuntimeError(msg)
    serve(*jobs)


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
    def pode_repetir(_job: Task[..., Any], _execucao: TaskRun, estado: State[Any]) -> bool:
        erro = estado.data if isinstance(estado.data, BaseException) else None
        # sem conseguir identificar a exceção, mantém o comportamento padrão (repetir)
        return not isinstance(erro, nao_repetir)

    return pode_repetir


__all__ = (
    "EstadoJob",
    "ExecucaoNaoEncontradaError",
    "OrquestradorIndisponivelError",
    "descobrir",
    "enfileirar",
    "id_execucao_atual",
    "job",
    "servir",
    "sessao_de_job",
    "status",
)
