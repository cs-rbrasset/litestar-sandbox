"""Lançamentos de extrato no modelo canônico, já traduzidos de qualquer custodiante.

Mesma regra da `carteira`: `referencia_origem` é o prefixo opaco do bruto no object storage,
nunca uma FK, e não há FK pra nenhuma outra área.
"""

import datetime
import decimal

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import CheckConstraint, Date, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.extrato.enums import TIPOS_LANCAMENTO

_TIPOS_SQL = ", ".join(f"'{tipo}'" for tipo in TIPOS_LANCAMENTO)


class LancamentoExtrato(BigIntAuditBase):
    """Um lançamento de um fundo numa data. Chave de negócio: (fundo, data, documento)."""

    __table_args__ = (
        UniqueConstraint(
            "fundo_cnpj", "data_referencia", "documento", name="uq_lancamento_extrato_chave"
        ),
        CheckConstraint(f"tipo IN ({_TIPOS_SQL})", name="tipo_valido"),
    )

    fundo_cnpj: Mapped[str] = mapped_column(String(14), index=True)
    data_referencia: Mapped[datetime.date] = mapped_column(Date, index=True)
    # identificador do lançamento no custodiante — é o que torna o upsert idempotente
    documento: Mapped[str] = mapped_column(String(64))
    tipo: Mapped[str] = mapped_column(String(32))
    descricao: Mapped[str] = mapped_column(String(255), default="")
    valor: Mapped[decimal.Decimal] = mapped_column(Numeric(28, 8))
    referencia_origem: Mapped[str] = mapped_column(String(255))
    coletado_em: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
