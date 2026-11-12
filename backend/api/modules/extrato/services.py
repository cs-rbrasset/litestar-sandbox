"""Regra de aplicação do extrato: validar o canônico e gravar."""

from typing import TYPE_CHECKING

from modules.extrato.domain import ExtratoNormalizado, validar
from modules.extrato.repositories import lancamentos_em, upsert_lancamentos

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.extrato.models import LancamentoExtrato


class ExtratoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(
        self,
        extrato: ExtratoNormalizado,
        referencia_origem: str,
        coletado_em: datetime.datetime,
        *,
        forcar: bool = False,
    ) -> int:
        validar(extrato)
        linhas = [
            {
                "fundo_cnpj": extrato.fundo_cnpj,
                "data_referencia": extrato.data_referencia,
                "documento": lancamento.documento,
                "tipo": lancamento.tipo.value,
                "descricao": lancamento.descricao,
                "valor": lancamento.valor,
                "referencia_origem": referencia_origem,
                "coletado_em": coletado_em,
            }
            for lancamento in extrato.lancamentos
        ]
        return await upsert_lancamentos(self._session, linhas, forcar=forcar)

    async def lancamentos_em(
        self, fundo_cnpj: str, data_referencia: datetime.date
    ) -> list[LancamentoExtrato]:
        return await lancamentos_em(self._session, fundo_cnpj, data_referencia)
