"""Regra de aplicação da carteira: validar o canônico e gravar.

A `carteira` é dona do conceito — ela valida e persiste. Quem entrega o canônico (o
`custodiante`, um upload manual, o que vier depois) não grava nada por conta própria.
"""

from typing import TYPE_CHECKING

from modules.carteira.domain import CarteiraNormalizada, validar
from modules.carteira.repositories import posicoes_em, upsert_posicoes

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.carteira.models import PosicaoCarteira


class CarteiraService:
    """Sem `SQLAlchemyAsyncRepositoryService`: a escrita aqui é upsert em lote, não CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(
        self,
        carteira: CarteiraNormalizada,
        referencia_origem: str,
        coletado_em: datetime.datetime,
        *,
        forcar: bool = False,
    ) -> int:
        """Valida e grava. Idempotente: rodar duas vezes com o mesmo bruto dá o mesmo estado."""
        validar(carteira)
        linhas = [
            {
                "fundo_cnpj": carteira.fundo_cnpj,
                "data_referencia": carteira.data_referencia,
                "classe": posicao.classe.value,
                "identificador": posicao.identificador,
                "descricao": posicao.descricao,
                "quantidade": posicao.quantidade,
                "valor": posicao.valor,
                "referencia_origem": referencia_origem,
                "coletado_em": coletado_em,
            }
            for posicao in carteira.posicoes
        ]
        return await upsert_posicoes(self._session, linhas, forcar=forcar)

    async def posicoes_em(
        self, fundo_cnpj: str, data_referencia: datetime.date
    ) -> list[PosicaoCarteira]:
        return await posicoes_em(self._session, fundo_cnpj, data_referencia)
