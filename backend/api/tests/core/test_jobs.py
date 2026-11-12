"""A porta de jobs: descoberta, política de retry por etapa, disparo e sessão por execução.

A maior parte não sobe server: o que se testa é o contrato que os módulos enxergam. Os testes
marcados com o fixture `orquestrador` executam um job de verdade, porque o retry por etapa é
comportamento do orquestrador — um dublê só provaria o dublê.
"""

import asyncio
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from prefect.exceptions import ObjectNotFound

from core import jobs
from modules.custodiante import tasks as custodiante

if TYPE_CHECKING:
    from pathlib import Path


def test_descobrir_acha_os_jobs_dos_modulos() -> None:
    """O worker, o `fluxos.py` e o `implantar.py` não dependem de lista escrita à mão."""
    nomes = {job.name for job in jobs.descobrir()}

    assert "custodiante-importar-carteira" in nomes
    assert "custodiante-reprocessar-carteira" in nomes
    assert "recompute-positions-report" in nomes


def test_job_nao_repete_quem_repete_e_a_etapa() -> None:
    """Repetir o job refaria as etapas que já deram certo — a coleta inclusive."""
    for job in jobs.descobrir():
        assert job.retries == 0, job.name


def test_cada_etapa_carrega_a_propria_politica() -> None:
    assert custodiante.baixar.retries == custodiante.TENTATIVAS_DE_COLETA
    assert custodiante.baixar.retry_delay_seconds == custodiante.INTERVALO_DE_COLETA_S
    # storage repete mais e mais rápido: o que está em jogo é não perder o que foi baixado
    assert custodiante.guardar.retries == custodiante.TENTATIVAS_DE_STORAGE
    assert custodiante.guardar.retry_delay_seconds == custodiante.INTERVALO_DE_STORAGE_S
    assert custodiante.gravar_carteira.retries == custodiante.TENTATIVAS_DE_GRAVACAO


def test_erro_de_dominio_nao_repete() -> None:
    """`nao_repetir` recebe tipos de exceção: o domínio não herda nada do core."""

    class LayoutError(ValueError):
        pass

    @jobs.etapa(tentativas=2, nao_repetir=(LayoutError,))
    async def _etapa() -> None: ...

    condicao = _etapa.retry_condition_fn
    assert condicao is not None
    assert condicao(_etapa, None, _EstadoFalho(LayoutError("layout"))) is False
    assert condicao(_etapa, None, _EstadoFalho(TimeoutError("rede caiu"))) is True


def test_sem_nao_repetir_nao_instala_condicao() -> None:
    @jobs.etapa(tentativas=2)
    async def _etapa() -> None: ...

    assert _etapa.retry_condition_fn is None


def test_nome_do_deployment_e_o_mesmo_em_dev_e_producao() -> None:
    assert (
        jobs.nome_do_deployment(custodiante.importar_carteira)
        == "custodiante-importar-carteira/padrao"
    )


def test_enfileirar_dispara_o_deployment_sem_esperar(monkeypatch: pytest.MonkeyPatch) -> None:
    chamada: dict[str, Any] = {}

    async def _arun_deployment(nome: str, **opcoes: Any) -> Any:
        chamada.update(nome=nome, **opcoes)
        return _Execucao("abc-123")

    monkeypatch.setattr(jobs, "arun_deployment", _arun_deployment)

    id_execucao = asyncio.run(jobs.enfileirar(custodiante.reprocessar_carteira, prefixo="p"))

    assert id_execucao == "abc-123"
    assert chamada["nome"] == "custodiante-reprocessar-carteira/padrao"
    assert chamada["parameters"] == {"prefixo": "p"}
    assert chamada["timeout"] == 0
    assert chamada["as_subflow"] is False


@pytest.mark.parametrize(
    ("erro", "esperado"),
    [
        (ObjectNotFound(None), jobs.JobNaoPublicadoError),
        (httpx.ConnectError("recusado"), jobs.OrquestradorIndisponivelError),
    ],
)
def test_enfileirar_traduz_falha_do_orquestrador(
    monkeypatch: pytest.MonkeyPatch, erro: Exception, esperado: type[Exception]
) -> None:
    """Job não publicado e orquestrador fora viram a mesma família de erro (503 na borda)."""

    async def _arun_deployment(_nome: str, **_opcoes: Any) -> Any:
        raise erro

    monkeypatch.setattr(jobs, "arun_deployment", _arun_deployment)

    with pytest.raises(esperado):
        asyncio.run(jobs.enfileirar(custodiante.reprocessar_carteira, prefixo="p"))
    assert issubclass(jobs.JobNaoPublicadoError, jobs.OrquestradorIndisponivelError)


def test_sessao_de_job_fecha_a_engine_que_abriu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Uma engine por execução, com dispose garantido — o processo não tem hook de shutdown."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/jobs.db")

    async def corpo() -> bool:
        async with jobs.sessao_de_job() as sessao:
            assert sessao is not None
        return jobs._execucao_atual.get() is None

    assert asyncio.run(corpo()) is True


@pytest.mark.usefixtures("orquestrador")
def test_falha_numa_etapa_repete_so_aquela_etapa() -> None:
    chamadas = {"primeira": 0, "segunda": 0}

    @jobs.etapa()
    async def primeira() -> str:
        chamadas["primeira"] += 1
        return "dado"

    @jobs.etapa(tentativas=2)
    async def segunda(dado: str) -> str:
        chamadas["segunda"] += 1
        if chamadas["segunda"] == 1:
            raise TimeoutError("blip")
        return dado.upper()

    @jobs.job("teste-repete-so-a-etapa")
    async def _job() -> str:
        return await segunda(await primeira())

    assert asyncio.run(_job()) == "DADO"
    assert chamadas == {"primeira": 1, "segunda": 2}


@pytest.mark.usefixtures("orquestrador")
def test_erro_de_dominio_falha_sem_repetir_de_verdade() -> None:
    """A condição de retry contra o estado que o orquestrador realmente entrega."""

    class LayoutError(ValueError):
        pass

    chamadas = {"etapa": 0}

    @jobs.etapa(tentativas=3, nao_repetir=(LayoutError,))
    async def parsear() -> None:
        chamadas["etapa"] += 1
        raise LayoutError("layout novo")

    @jobs.job("teste-dominio-nao-repete")
    async def _job() -> None:
        await parsear()

    with pytest.raises(LayoutError):
        asyncio.run(_job())
    assert chamadas["etapa"] == 1


class _EstadoFalho:
    """Dublê do estado que o orquestrador passa pra condição de retry."""

    def __init__(self, erro: BaseException) -> None:
        self.data = erro


class _Execucao:
    def __init__(self, id_execucao: str) -> None:
        self.id = id_execucao
