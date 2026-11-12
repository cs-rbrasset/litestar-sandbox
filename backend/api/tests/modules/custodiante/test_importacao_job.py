"""O fluxo do job de ponta a ponta, com gateway dublê e storage em memória.

O que este arquivo trava: as etapas **não se fundem**. Baixar, guardar o bruto, parsear e
registrar são quatro passos, nessa ordem, e o bruto é gravado **antes** do parse — é o que
torna o reprocessamento possível quando um parser está errado.

Nada de Prefect no ar: chama-se `.fn` do job, que é a função que o worker executaria.
"""

import asyncio
import datetime
import pathlib
from typing import TYPE_CHECKING, Any

import pytest

from core.storage import ArmazenamentoEmMemoria
from modules.carteira.services import CarteiraService
from modules.custodiante import tasks
from modules.custodiante.brutos import MANIFESTO
from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.parsers import btg as parser_btg
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError
from modules.custodiante.protocols import Adaptador, ArquivoBruto

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

    from core.settings import DatabaseSettings

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
FUNDO = "12345678000190"
DATA = datetime.date(2026, 10, 31)


class GatewayFake:
    """Só I/O, como o de verdade — aqui, I/O que vem de um arquivo do repositório."""

    codigo = CodigoCustodiante.BTG

    def __init__(self, conteudo: bytes) -> None:
        self._conteudo = conteudo
        self.chamadas: list[tuple[str, datetime.date]] = []

    async def baixar_carteira(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        self.chamadas.append((fundo_cnpj, data))
        return [ArquivoBruto(nome="carteira.xml", conteudo=self._conteudo, formato="xml")]

    async def baixar_extrato(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        raise NotImplementedError


@pytest.fixture
def armazenamento(monkeypatch: pytest.MonkeyPatch) -> ArmazenamentoEmMemoria:
    memoria = ArmazenamentoEmMemoria()
    monkeypatch.setattr(tasks, "armazenamento_padrao", lambda: memoria)
    return memoria


@pytest.fixture
def banco_do_job(
    monkeypatch: pytest.MonkeyPatch,
    database_settings: DatabaseSettings,
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    """O job abre a própria sessão a partir do ambiente — aqui, o SQLite do `tmp_path`."""
    monkeypatch.setenv("DATABASE_URL", database_settings.database_url)

    async def criar_tabelas(_sessao: AsyncSession) -> None:
        return None

    rodar_com_sessao(criar_tabelas)


def _com_gateway(monkeypatch: pytest.MonkeyPatch, gateway: GatewayFake) -> GatewayFake:
    monkeypatch.setattr(
        tasks,
        "adaptador",
        lambda _codigo: Adaptador(gateway=gateway, parse_carteira=parser_btg.parse_carteira),
    )
    return gateway


@pytest.fixture
def gateway(monkeypatch: pytest.MonkeyPatch) -> GatewayFake:
    return _com_gateway(
        monkeypatch, GatewayFake((FIXTURES / "carteira_btg.xml").read_bytes())
    )


@pytest.mark.usefixtures("banco_do_job")
def test_importacao_baixa_guarda_parseia_e_registra(
    armazenamento: ArmazenamentoEmMemoria,
    gateway: GatewayFake,
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    prefixo = asyncio.run(
        tasks.importar_carteira.fn(codigo=CodigoCustodiante.BTG.value, fundo_cnpj=FUNDO, data=DATA)
    )

    assert gateway.chamadas == [(FUNDO, DATA)]
    assert prefixo.startswith(f"custodiante/btg/carteira/{FUNDO}/2026-10-31/")
    assert f"{prefixo}/carteira.xml" in armazenamento.objetos
    assert f"{prefixo}/{MANIFESTO}" in armazenamento.objetos

    async def ler(sessao: AsyncSession) -> list[Any]:
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    posicoes = rodar_com_sessao(ler)
    assert len(posicoes) == 4
    assert {p.referencia_origem for p in posicoes} == {prefixo}


@pytest.mark.usefixtures("banco_do_job")
def test_bruto_fica_guardado_mesmo_quando_o_parse_quebra(
    armazenamento: ArmazenamentoEmMemoria, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O passo 2 vem antes do 3 justamente por isso: o arquivo que quebrou é o que se reprocessa."""
    _com_gateway(monkeypatch, GatewayFake(b"<arquivoposicao><fundo/></arquivoposicao>"))

    with pytest.raises(LayoutNaoReconhecidoError):
        asyncio.run(
            tasks.importar_carteira.fn(
                codigo=CodigoCustodiante.BTG.value, fundo_cnpj=FUNDO, data=DATA
            )
        )

    guardados = [caminho for caminho in armazenamento.objetos if caminho.endswith("carteira.xml")]
    assert guardados, "o bruto tem que ser gravado antes do parse"


@pytest.mark.usefixtures("banco_do_job")
def test_reprocessamento_nao_chama_o_custodiante(
    armazenamento: ArmazenamentoEmMemoria,
    gateway: GatewayFake,
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    prefixo = asyncio.run(
        tasks.importar_carteira.fn(codigo=CodigoCustodiante.BTG.value, fundo_cnpj=FUNDO, data=DATA)
    )
    chamadas_apos_importar = len(gateway.chamadas)

    asyncio.run(tasks.reprocessar_carteira.fn(prefixo=prefixo))

    assert len(gateway.chamadas) == chamadas_apos_importar, "reprocessar lê o bruto, não coleta"

    async def ler(sessao: AsyncSession) -> list[Any]:
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    assert len(rodar_com_sessao(ler)) == 4
