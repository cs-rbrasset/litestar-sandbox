"""Modelo canônico de extrato. Mesmo papel do canônico de carteira, para o outro documento.

Puro: sem banco, sem HTTP, sem `database`, sem orquestrador. `database/models/extrato/enums.py`
tem a cópia do vocabulário pro CHECK da tabela, e um teste compara as duas.
"""

import dataclasses
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    import decimal


class TipoLancamento(StrEnum):
    APLICACAO = "aplicacao"
    RESGATE = "resgate"
    LIQUIDACAO = "liquidacao"
    TARIFA = "tarifa"
    RENDIMENTO = "rendimento"
    TRANSFERENCIA = "transferencia"
    OUTRO = "outro"


@dataclasses.dataclass(frozen=True, slots=True)
class LancamentoNormalizado:
    documento: str
    tipo: TipoLancamento
    valor: decimal.Decimal
    descricao: str = ""


@dataclasses.dataclass(frozen=True, slots=True)
class ExtratoNormalizado:
    """Só o que veio do documento — hora e origem da coleta viajam com o `registrar_extrato`."""

    fundo_cnpj: str
    data_referencia: datetime.date
    lancamentos: tuple[LancamentoNormalizado, ...]


class ExtratoInvalidoError(ValueError):
    """Extrato que não passa na validação estrutural — repetir o job não resolve."""


def validar(extrato: ExtratoNormalizado) -> None:
    """Validação estrutural. [AJUSTAR: regras de validação do extrato] com quem entende."""
    problemas: list[str] = []
    if not (len(extrato.fundo_cnpj) == 14 and extrato.fundo_cnpj.isdigit()):
        problemas.append(f"fundo_cnpj inválido: {extrato.fundo_cnpj!r}")
    documentos = [lancamento.documento for lancamento in extrato.lancamentos]
    if len(documentos) != len(set(documentos)):
        problemas.append("documento repetido no mesmo extrato")
    if problemas:
        raise ExtratoInvalidoError("; ".join(problemas))
