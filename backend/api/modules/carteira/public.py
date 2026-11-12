"""Superfície que outros módulos podem usar da `carteira` — e nada além disso.

Duas coisas: o **modelo canônico** (o formato que qualquer fonte tem que produzir) e
`registrar_carteira` (validar + gravar). Quem produz carteira — o `custodiante` hoje, um upload
manual amanhã — entrega o canônico aqui e guarda o próprio bruto; a `carteira` não sabe que
custodiantes existem.

O import de `services` é adiado de propósito: assim este arquivo continua **puro** no nível de
módulo (sem sqlalchemy), e `custodiante.parsers` pode importar o canônico daqui sem quebrar a
regra de pureza dos parsers.
"""

from typing import TYPE_CHECKING

from modules.carteira.domain import (
    CarteiraInvalidaError,
    CarteiraNormalizada,
    ClasseAtivo,
    PosicaoNormalizada,
)

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_carteira(
    session: AsyncSession,
    carteira: CarteiraNormalizada,
    referencia_origem: str,
    coletado_em: datetime.datetime,
    *,
    forcar: bool = False,
) -> int:
    """Valida e grava a carteira; devolve quantas posições foram enviadas.

    `referencia_origem` é opaca pra `carteira` (hoje, o prefixo do bruto no object storage):
    guardada pra rastreabilidade, nunca lida nem usada como FK. `coletado_em` é a hora da
    coleta que produziu esse bruto — é ela que decide a precedência na gravação.
    """
    from modules.carteira.services import CarteiraService  # noqa: PLC0415

    return await CarteiraService(session).registrar(
        carteira, referencia_origem, coletado_em, forcar=forcar
    )


__all__ = (
    "CarteiraInvalidaError",
    "CarteiraNormalizada",
    "ClasseAtivo",
    "PosicaoNormalizada",
    "registrar_carteira",
)
