"""Superfície pública do `extrato` — canônico + `registrar_extrato`.

Mesma forma do `carteira/public.py`, inclusive o import adiado de `services`: mantém este
arquivo puro no nível de módulo pra que `custodiante.parsers` possa importar o canônico.
"""

from typing import TYPE_CHECKING

from modules.extrato.domain import (
    ExtratoInvalidoError,
    ExtratoNormalizado,
    LancamentoNormalizado,
    TipoLancamento,
)

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_extrato(
    session: AsyncSession,
    extrato: ExtratoNormalizado,
    referencia_origem: str,
    coletado_em: datetime.datetime,
    *,
    forcar: bool = False,
) -> int:
    from modules.extrato.services import ExtratoService  # noqa: PLC0415

    return await ExtratoService(session).registrar(
        extrato, referencia_origem, coletado_em, forcar=forcar
    )


__all__ = (
    "ExtratoInvalidoError",
    "ExtratoNormalizado",
    "LancamentoNormalizado",
    "TipoLancamento",
    "registrar_extrato",
)
