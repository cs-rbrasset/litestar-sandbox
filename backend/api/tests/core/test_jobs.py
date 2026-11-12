"""A porta de jobs: descoberta, política de retry e sessão por execução.

Não sobe server nem worker do orquestrador — o que se testa aqui é o contrato que os módulos
enxergam, que é tudo o que eles conhecem.
"""

import asyncio
from typing import TYPE_CHECKING

from core import jobs
from modules.custodiante.tasks import importar_carteira, reprocessar_carteira

if TYPE_CHECKING:
    import pytest


def test_descobrir_acha_os_jobs_dos_modulos() -> None:
    """O worker e o autowire não dependem de lista escrita à mão em lugar nenhum."""
    nomes = {job.name for job in jobs.descobrir()}

    assert "custodiante-importar-carteira" in nomes
    assert "custodiante-reprocessar-carteira" in nomes
    assert "recompute-positions-report" in nomes


def test_job_declarado_carrega_a_politica_de_retry() -> None:
    assert importar_carteira.retries == 3
    assert importar_carteira.retry_delay_seconds == 60
    # reprocessar não fala com o custodiante: não há falha de coleta pra repetir
    assert reprocessar_carteira.retries == 0


def test_erro_de_dominio_nao_repete() -> None:
    """`nao_repetir` recebe tipos de exceção: o domínio não herda nada do core."""

    class LayoutError(ValueError):
        pass

    @jobs.job("teste-nao-repetir", nao_repetir=(LayoutError,))
    async def _job() -> None: ...

    condicao = _job.retry_condition_fn
    assert condicao is not None
    assert condicao(_job, None, _EstadoFalho(LayoutError("layout"))) is False
    assert condicao(_job, None, _EstadoFalho(TimeoutError("rede caiu"))) is True


def test_sem_nao_repetir_nao_instala_condicao() -> None:
    @jobs.job("teste-sem-condicao")
    async def _job() -> None: ...

    assert _job.retry_condition_fn is None


def test_sessao_de_job_fecha_a_engine_que_abriu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """Uma engine por execução, com dispose garantido — o worker não tem hook de shutdown."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/jobs.db")

    async def corpo() -> bool:
        async with jobs.sessao_de_job() as sessao:
            assert sessao is not None
        return jobs._execucao_atual.get() is None

    assert asyncio.run(corpo()) is True


class _EstadoFalho:
    """Dublê do estado que o orquestrador passa pra condição de retry."""

    def __init__(self, erro: BaseException) -> None:
        self.data = erro
