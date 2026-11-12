"""Vocabulário do `custodiante`. Não é shim: este módulo não tem área no `database`.

O bruto mora no object storage e a carteira/extrato guardam só uma referência opaca — não
existe tabela de custodiante, então não existe `database/models/custodiante/`.
"""

from enum import StrEnum


class CodigoCustodiante(StrEnum):
    """Um por custodiante integrado. O valor entra no caminho do bruto no storage."""

    BTG = "btg"  # [exemplo] API → XML
    PORTAL_XPTO = "portal_xpto"  # [exemplo] scraping → HTML


class TipoDocumento(StrEnum):
    CARTEIRA = "carteira"
    EXTRATO = "extrato"


__all__ = ("CodigoCustodiante", "TipoDocumento")
