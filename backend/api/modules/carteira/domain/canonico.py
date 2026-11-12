"""Modelo canônico de carteira — o formato que todo custodiante tem que virar.

Puro de propósito: sem banco, sem HTTP, sem `database`, sem orquestrador. É o que o parser
devolve, o que o `public.py` aceita e o que dá pra testar sem fixture nenhuma.

O vocabulário de `ClasseAtivo` é a fonte de verdade; `database/models/carteira/enums.py` tem
uma cópia pro CHECK da tabela, e um teste compara as duas (a regra de pureza impede os dois
lados de se importarem).

[AJUSTAR: riqueza do modelo canônico por classe de ativo] — o XML ANBIMA separa títulos
públicos, privados, compromissadas, cotas, derivativos e provisões, cada um com campos
próprios (indexador, taxa, vencimento, contraparte...). Aqui está o mínimo comum; quem entende
de carteira de fundos decide o que mais sobe pro canônico.
"""

import dataclasses
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    import decimal
    from collections.abc import Iterable


class ClasseAtivo(StrEnum):
    TITULO_PUBLICO = "titulo_publico"
    TITULO_PRIVADO = "titulo_privado"
    COMPROMISSADA = "compromissada"
    COTA = "cota"
    DERIVATIVO = "derivativo"
    PROVISAO = "provisao"
    CAIXA = "caixa"
    OUTRO = "outro"


@dataclasses.dataclass(frozen=True, slots=True)
class PosicaoNormalizada:
    classe: ClasseAtivo
    identificador: str
    quantidade: decimal.Decimal
    valor: decimal.Decimal
    descricao: str = ""


@dataclasses.dataclass(frozen=True, slots=True)
class CarteiraNormalizada:
    """Só o que veio do documento.

    Quando a coleta aconteceu e de onde ela veio **não** moram aqui: são metadado da coleta,
    entregues ao `registrar_carteira` junto com o canônico. É o que mantém o parser
    determinístico e o reprocessamento fiel à precedência original.
    """

    fundo_cnpj: str
    data_referencia: datetime.date
    posicoes: tuple[PosicaoNormalizada, ...]
    patrimonio_liquido: decimal.Decimal | None = None


class CarteiraInvalidaError(ValueError):
    """Carteira que não passa na validação estrutural — repetir o job não resolve."""


def validar(carteira: CarteiraNormalizada) -> None:
    """Validação **estrutural**, não financeira.

    [AJUSTAR: regras de validação da carteira] — a regra "soma das posições = PL" está errada:
    o PL inclui caixa, provisões, valores a pagar e a receber. Definir com quem entende de
    carteira de fundos antes de escrever qualquer conferência de total aqui.
    """
    problemas: list[str] = []
    if not (len(carteira.fundo_cnpj) == 14 and carteira.fundo_cnpj.isdigit()):
        problemas.append(f"fundo_cnpj inválido: {carteira.fundo_cnpj!r}")
    if not carteira.posicoes:
        problemas.append("carteira sem posições")
    repetidas = _repetidas(carteira.posicoes)
    if repetidas:
        problemas.append(f"posições repetidas na mesma carteira: {sorted(repetidas)}")
    if problemas:
        raise CarteiraInvalidaError("; ".join(problemas))


def _repetidas(posicoes: Iterable[PosicaoNormalizada]) -> set[str]:
    vistas: set[tuple[str, str]] = set()
    repetidas: set[str] = set()
    for posicao in posicoes:
        chave = (posicao.classe.value, posicao.identificador)
        if chave in vistas:
            repetidas.add(posicao.identificador)
        vistas.add(chave)
    return repetidas
