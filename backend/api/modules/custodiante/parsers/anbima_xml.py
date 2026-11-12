"""Base comum do XML no layout ANBIMA — a parte que vários custodiantes compartilham.

Função pura: bytes → canônico. Sem I/O, sem banco, sem orquestrador. O parser de cada
custodiante (`parsers/btg.py`, etc.) escolhe o arquivo certo e chama daqui.

Simplificação assumida: só `codigo`, `quantidade` e `valor` por posição.
[AJUSTAR: riqueza do modelo canônico por classe de ativo] — o layout real separa indexador,
taxa, vencimento, contraparte e mais, por classe.
"""

import datetime
import decimal
from typing import TYPE_CHECKING
from xml.etree import ElementTree

from modules.carteira.public import CarteiraNormalizada, ClasseAtivo, PosicaoNormalizada
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError

if TYPE_CHECKING:
    from collections.abc import Iterator

#: tag do elemento no XML → classe no canônico. Tag desconhecida vira `OUTRO`, nunca erro:
#: um custodiante que acrescenta uma seção não pode derrubar a importação inteira.
CLASSE_POR_TAG = {
    "titpublico": ClasseAtivo.TITULO_PUBLICO,
    "titprivado": ClasseAtivo.TITULO_PRIVADO,
    "compromissada": ClasseAtivo.COMPROMISSADA,
    "cota": ClasseAtivo.COTA,
    "derivativo": ClasseAtivo.DERIVATIVO,
    "provisao": ClasseAtivo.PROVISAO,
    "caixa": ClasseAtivo.CAIXA,
}


def ler_carteira(conteudo: bytes) -> CarteiraNormalizada:
    """Determinístico: mesmo arquivo, mesmo resultado.

    A hora da coleta **não** entra aqui — ela é metadado da coleta, não da carteira, e viaja
    junto com a referência da origem até o `registrar_carteira`. É isso que faz reprocessar um
    bruto antigo preservar a precedência original em vez de parecer uma coleta nova.
    """
    raiz = _raiz(conteudo)
    fundo = raiz.find("fundo")
    if fundo is None:
        msg = "XML sem elemento <fundo>"
        raise LayoutNaoReconhecidoError(msg)
    cabecalho = fundo.find("header")
    if cabecalho is None:
        msg = "XML sem elemento <header>"
        raise LayoutNaoReconhecidoError(msg)
    return CarteiraNormalizada(
        fundo_cnpj=_texto(cabecalho, "cnpj"),
        data_referencia=_data(_texto(cabecalho, "dtposicao")),
        patrimonio_liquido=_decimal_opcional(cabecalho, "patliq"),
        posicoes=tuple(_posicoes(fundo)),
    )


def _raiz(conteudo: bytes) -> ElementTree.Element:
    try:
        # entrada externa: `ElementTree` não expande entidade externa por padrão no CPython,
        # mas se o volume/origem crescer, trocar por `defusedxml` é a medida certa.
        return ElementTree.fromstring(conteudo)  # noqa: S314
    except ElementTree.ParseError as erro:
        msg = f"XML malformado: {erro}"
        raise LayoutNaoReconhecidoError(msg) from erro


def _posicoes(fundo: ElementTree.Element) -> Iterator[PosicaoNormalizada]:
    for elemento in fundo:
        if elemento.tag == "header":
            continue
        yield PosicaoNormalizada(
            classe=CLASSE_POR_TAG.get(elemento.tag, ClasseAtivo.OUTRO),
            identificador=_texto(elemento, "codigo"),
            descricao=_texto_opcional(elemento, "descricao"),
            quantidade=_decimal(elemento, "quantidade"),
            valor=_decimal(elemento, "valor"),
        )


def _texto(elemento: ElementTree.Element, campo: str) -> str:
    filho = elemento.find(campo)
    if filho is None or not (filho.text or "").strip():
        msg = f"campo <{campo}> ausente ou vazio em <{elemento.tag}>"
        raise LayoutNaoReconhecidoError(msg)
    return (filho.text or "").strip()


def _texto_opcional(elemento: ElementTree.Element, campo: str) -> str:
    filho = elemento.find(campo)
    return (filho.text or "").strip() if filho is not None else ""


def _decimal(elemento: ElementTree.Element, campo: str) -> decimal.Decimal:
    bruto = _texto(elemento, campo)
    try:
        return decimal.Decimal(bruto)
    except decimal.InvalidOperation as erro:
        msg = f"campo <{campo}> não é número em <{elemento.tag}>: {bruto!r}"
        raise LayoutNaoReconhecidoError(msg) from erro


def _decimal_opcional(elemento: ElementTree.Element, campo: str) -> decimal.Decimal | None:
    filho = elemento.find(campo)
    return _decimal(elemento, campo) if filho is not None else None


def _data(bruto: str) -> datetime.date:
    try:
        return datetime.datetime.strptime(bruto, "%Y%m%d").replace(tzinfo=datetime.UTC).date()
    except ValueError as erro:
        msg = f"data de posição fora do formato AAAAMMDD: {bruto!r}"
        raise LayoutNaoReconhecidoError(msg) from erro
