"""Gravação da carteira: idempotência e precedência por `coletado_em`.

É a parte que um retry do orquestrador ou um reprocessamento exercita de verdade — e a que
quebra silenciosamente se alguém trocar o upsert por "busca e depois insere".
"""

import datetime
import decimal
from typing import TYPE_CHECKING, Any

from modules.carteira.public import (
    CarteiraNormalizada,
    ClasseAtivo,
    PosicaoNormalizada,
    registrar_carteira,
)
from modules.carteira.services import CarteiraService

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

FUNDO = "12345678000190"
DATA = datetime.date(2026, 10, 31)
ONTEM = datetime.datetime(2026, 10, 31, 8, 0, tzinfo=datetime.UTC)
HOJE = datetime.datetime(2026, 11, 1, 8, 0, tzinfo=datetime.UTC)


def _carteira(valor: str) -> CarteiraNormalizada:
    return CarteiraNormalizada(
        fundo_cnpj=FUNDO,
        data_referencia=DATA,
        posicoes=(
            PosicaoNormalizada(
                classe=ClasseAtivo.TITULO_PUBLICO,
                identificador="LTN2027",
                quantidade=decimal.Decimal("100"),
                valor=decimal.Decimal(valor),
                descricao="LTN 2027",
            ),
        ),
    )


def test_gravar_duas_vezes_o_mesmo_bruto_nao_duplica(
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    async def corpo(sessao: AsyncSession) -> list[Any]:
        await registrar_carteira(sessao, _carteira("95000.00"), "prefixo/a", ONTEM)
        await registrar_carteira(sessao, _carteira("95000.00"), "prefixo/a", ONTEM)
        await sessao.commit()
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    posicoes = rodar_com_sessao(corpo)

    assert len(posicoes) == 1
    assert posicoes[0].valor == decimal.Decimal("95000.00")


def test_coleta_mais_nova_sobrescreve(
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    async def corpo(sessao: AsyncSession) -> list[Any]:
        await registrar_carteira(sessao, _carteira("95000.00"), "prefixo/a", ONTEM)
        await registrar_carteira(sessao, _carteira("96000.00"), "prefixo/b", HOJE)
        await sessao.commit()
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    posicoes = rodar_com_sessao(corpo)

    assert posicoes[0].valor == decimal.Decimal("96000.00")
    assert posicoes[0].referencia_origem == "prefixo/b"


def test_coleta_mais_antiga_nao_sobrescreve(
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    """Chegar atrasado não pode rebaixar o que já está gravado."""

    async def corpo(sessao: AsyncSession) -> list[Any]:
        await registrar_carteira(sessao, _carteira("96000.00"), "prefixo/b", HOJE)
        await registrar_carteira(sessao, _carteira("95000.00"), "prefixo/a", ONTEM)
        await sessao.commit()
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    posicoes = rodar_com_sessao(corpo)

    assert posicoes[0].valor == decimal.Decimal("96000.00")
    assert posicoes[0].referencia_origem == "prefixo/b"


def test_reprocessamento_forcado_sobrescreve_mesmo_sendo_mais_antigo(
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    """O único caminho pra uma releitura antiga vencer: alguém pediu explicitamente."""

    async def corpo(sessao: AsyncSession) -> list[Any]:
        await registrar_carteira(sessao, _carteira("96000.00"), "prefixo/b", HOJE)
        await registrar_carteira(
            sessao, _carteira("95000.00"), "prefixo/a", ONTEM, forcar=True
        )
        await sessao.commit()
        return await CarteiraService(sessao).posicoes_em(FUNDO, DATA)

    posicoes = rodar_com_sessao(corpo)

    assert posicoes[0].valor == decimal.Decimal("95000.00")
    assert posicoes[0].referencia_origem == "prefixo/a"
