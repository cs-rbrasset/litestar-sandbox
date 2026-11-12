"""Posições de carteira no modelo canônico, já traduzidas de qualquer custodiante.

A carteira guarda só uma **referência opaca** à origem (`referencia_origem`, o prefixo do
bruto no object storage): não lê o bruto, não sabe que custodiantes existem e não tem FK pra
nada fora desta área.

[AJUSTAR: confirmar tabelas × JSONB] — hoje cada posição é uma linha. Se o modelo canônico
ficar muito mais rico por classe de ativo (o XML ANBIMA separa títulos públicos, privados,
compromissadas, cotas, derivativos e provisões), parte disso pode virar JSONB em vez de coluna.
"""

import datetime
import decimal

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.carteira.enums import CLASSES_ATIVO

_CLASSES_SQL = ", ".join(f"'{classe}'" for classe in CLASSES_ATIVO)


class PosicaoCarteira(BigIntAuditBase):
    """Uma posição de um fundo numa data. Chave de negócio: (fundo, data, classe, id do ativo)."""

    __table_args__ = (
        UniqueConstraint(
            "fundo_cnpj",
            "data_referencia",
            "classe",
            "identificador",
            name="uq_posicao_carteira_chave",
        ),
        CheckConstraint(f"classe IN ({_CLASSES_SQL})", name="classe_valida"),
    )

    fundo_cnpj: Mapped[str] = mapped_column(String(14), index=True)
    data_referencia: Mapped[datetime.date] = mapped_column(Date, index=True)
    classe: Mapped[str] = mapped_column(String(32))
    identificador: Mapped[str] = mapped_column(String(64))
    descricao: Mapped[str] = mapped_column(String(255), default="")
    quantidade: Mapped[decimal.Decimal] = mapped_column(Numeric(28, 8))
    valor: Mapped[decimal.Decimal] = mapped_column(Numeric(28, 8))
    # prefixo do bruto no object storage — string opaca de propósito, nunca uma FK
    referencia_origem: Mapped[str] = mapped_column(String(255))
    # precedência: só sobrescreve quando a coleta nova é mais recente que a gravada
    coletado_em: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
