"""Upsert idempotente do extrato — mesma forma do `carteira/repositories.py`."""

from typing import TYPE_CHECKING, Any

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as insert_postgresql
from sqlalchemy.dialects.sqlite import insert as insert_sqlite

from modules.extrato.models import LancamentoExtrato

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

_CHAVE = ("fundo_cnpj", "data_referencia", "documento")
_ATUALIZAVEIS = ("tipo", "descricao", "valor", "referencia_origem", "coletado_em")


class LancamentoExtratoRepository(SQLAlchemyAsyncRepository[LancamentoExtrato]):
    model_type = LancamentoExtrato


def _dialeto(session: AsyncSession) -> str:
    bind = session.bind if session.bind is not None else session.get_bind()
    return bind.dialect.name


async def upsert_lancamentos(
    session: AsyncSession, linhas: list[dict[str, Any]], *, forcar: bool = False
) -> int:
    if not linhas:
        return 0
    insert = insert_postgresql if _dialeto(session) == "postgresql" else insert_sqlite
    comando = insert(LancamentoExtrato).values(linhas)
    excluded = comando.excluded
    comando = comando.on_conflict_do_update(
        index_elements=list(_CHAVE),
        set_={coluna: excluded[coluna] for coluna in _ATUALIZAVEIS},
        where=None if forcar else LancamentoExtrato.coletado_em < excluded.coletado_em,
    )
    await session.execute(comando)
    return len(linhas)


async def lancamentos_em(
    session: AsyncSession, fundo_cnpj: str, data_referencia: datetime.date
) -> list[LancamentoExtrato]:
    resultado = await session.execute(
        select(LancamentoExtrato)
        .where(
            LancamentoExtrato.fundo_cnpj == fundo_cnpj,
            LancamentoExtrato.data_referencia == data_referencia,
        )
        .order_by(LancamentoExtrato.documento)
    )
    return list(resultado.scalars())
