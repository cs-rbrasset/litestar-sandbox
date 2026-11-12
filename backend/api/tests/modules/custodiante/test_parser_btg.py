"""Parser contra fixture: sem rede, sem banco, sem orquestrador.

Toda fixture é um arquivo de verdade (ou um recorte dele), não um dicionário montado à mão —
é o único jeito de o teste falhar quando o custodiante mudar o layout.
"""

import datetime
import decimal
import pathlib

import pytest

from modules.carteira.domain import ClasseAtivo
from modules.custodiante.parsers import btg
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError
from modules.custodiante.protocols import ArquivoBruto

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _arquivo(nome: str = "carteira_btg.xml", formato: str = "xml") -> ArquivoBruto:
    return ArquivoBruto(nome=nome, conteudo=(FIXTURES / nome).read_bytes(), formato=formato)


def test_le_cabecalho_e_posicoes_da_fixture() -> None:
    carteira = btg.parse_carteira([_arquivo()])

    assert carteira.fundo_cnpj == "12345678000190"
    assert carteira.data_referencia == datetime.date(2026, 10, 31)
    assert carteira.patrimonio_liquido == decimal.Decimal("1250000.00")
    assert len(carteira.posicoes) == 4


def test_mapeia_a_secao_do_xml_para_a_classe_do_canonico() -> None:
    carteira = btg.parse_carteira([_arquivo()])
    por_identificador = {p.identificador: p for p in carteira.posicoes}

    assert por_identificador["LTN2027"].classe is ClasseAtivo.TITULO_PUBLICO
    assert por_identificador["CRI22A"].classe is ClasseAtivo.TITULO_PRIVADO
    assert por_identificador["CAIXA"].classe is ClasseAtivo.CAIXA


def test_secao_desconhecida_vira_outro_em_vez_de_derrubar_a_importacao() -> None:
    carteira = btg.parse_carteira([_arquivo()])
    por_identificador = {p.identificador: p for p in carteira.posicoes}

    assert por_identificador["NOVIDADE"].classe is ClasseAtivo.OUTRO


def test_valores_viram_decimal_e_nao_float() -> None:
    carteira = btg.parse_carteira([_arquivo()])
    posicao = next(p for p in carteira.posicoes if p.identificador == "LTN2027")

    assert posicao.quantidade == decimal.Decimal("1000")
    assert posicao.valor == decimal.Decimal("950000.00")


def test_parser_e_deterministico() -> None:
    """Sem `now()` lá dentro: a hora da coleta é metadado do job, não do arquivo."""
    assert btg.parse_carteira([_arquivo()]) == btg.parse_carteira([_arquivo()])


def test_sem_xml_e_erro_de_layout_nao_de_coleta() -> None:
    html = ArquivoBruto(nome="pagina.html", conteudo=b"<html></html>", formato="html")

    with pytest.raises(LayoutNaoReconhecidoError):
        btg.parse_carteira([html])


def test_xml_malformado_e_erro_de_layout() -> None:
    quebrado = ArquivoBruto(nome="x.xml", conteudo=b"<arquivoposicao>", formato="xml")

    with pytest.raises(LayoutNaoReconhecidoError, match="malformado"):
        btg.parse_carteira([quebrado])


def test_campo_obrigatorio_ausente_e_erro_de_layout() -> None:
    sem_header = ArquivoBruto(
        nome="x.xml", conteudo=b"<arquivoposicao><fundo/></arquivoposicao>", formato="xml"
    )

    with pytest.raises(LayoutNaoReconhecidoError, match="header"):
        btg.parse_carteira([sem_header])
