"""Acesso a dado de carteira, incluindo o upsert idempotente.

`INSERT ... ON CONFLICT`, nunca "busca e depois insere": o job pode rodar duas vezes (retry do
orquestrador, reprocessamento) e o resultado tem que ser o mesmo.
"""

from typing import TYPE_CHECKING, Any

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as insert_postgresql
from sqlalchemy.dialects.sqlite import insert as insert_sqlite

from modules.carteira.models import PosicaoCarteira

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

_CHAVE = ("fundo_cnpj", "data_referencia", "classe", "identificador")
_ATUALIZAVEIS = ("quantidade", "valor", "descricao", "referencia_origem", "coletado_em")


class PosicaoCarteiraRepository(SQLAlchemyAsyncRepository[PosicaoCarteira]):
    model_type = PosicaoCarteira


def _dialeto(session: AsyncSession) -> str:
    """O `ON CONFLICT` é a mesma sintaxe nos dois, mas vem de construtores diferentes."""
    bind = session.bind if session.bind is not None else session.get_bind()
    return bind.dialect.name


async def upsert_posicoes(
    session: AsyncSession, linhas: list[dict[str, Any]], *, forcar: bool = False
) -> int:
    """Grava as posições; devolve quantas linhas foram enviadas.

    Precedência: só sobrescreve o que já está gravado quando a coleta nova é **mais recente**
    (`coletado_em`). `forcar=True` ignora isso — é o reprocessamento explícito, quando o parser
    foi corrigido e o bruto antigo vale mais que a linha gravada.
    """
    if not linhas:
        return 0
    insert = insert_postgresql if _dialeto(session) == "postgresql" else insert_sqlite
    comando = insert(PosicaoCarteira).values(linhas)
    excluded = comando.excluded
    comando = comando.on_conflict_do_update(
        index_elements=list(_CHAVE),
        set_={coluna: excluded[coluna] for coluna in _ATUALIZAVEIS},
        where=None if forcar else PosicaoCarteira.coletado_em < excluded.coletado_em,
    )
    await session.execute(comando)
    return len(linhas)


async def posicoes_em(
    session: AsyncSession, fundo_cnpj: str, data_referencia: datetime.date
) -> list[PosicaoCarteira]:
    resultado = await session.execute(
        select(PosicaoCarteira)
        .where(
            PosicaoCarteira.fundo_cnpj == fundo_cnpj,
            PosicaoCarteira.data_referencia == data_referencia,
        )
        .order_by(PosicaoCarteira.classe, PosicaoCarteira.identificador)
    )
    return list(resultado.scalars())
