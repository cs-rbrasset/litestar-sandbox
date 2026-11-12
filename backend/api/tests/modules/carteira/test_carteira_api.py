"""A borda HTTP da carteira é só leitura — escrever é trabalho do job, não de uma rota."""

import datetime
import decimal
from typing import TYPE_CHECKING, Any

from litestar.testing import TestClient

from modules.carteira.public import (
    CarteiraNormalizada,
    ClasseAtivo,
    PosicaoNormalizada,
    registrar_carteira,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncSession

FUNDO = "12345678000190"
DATA = datetime.date(2026, 10, 31)
COLETADO_EM = datetime.datetime(2026, 11, 1, 8, 0, tzinfo=datetime.UTC)


def test_consulta_devolve_as_posicoes_gravadas(
    app_client: TestClient[Litestar],
    rodar_com_sessao: Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any],
) -> None:
    async def gravar(sessao: AsyncSession) -> None:
        carteira = CarteiraNormalizada(
            fundo_cnpj=FUNDO,
            data_referencia=DATA,
            posicoes=(
                PosicaoNormalizada(
                    classe=ClasseAtivo.TITULO_PUBLICO,
                    identificador="LTN2027",
                    quantidade=decimal.Decimal("1000"),
                    valor=decimal.Decimal("950000.00"),
                    descricao="LTN 01/01/2027",
                ),
            ),
        )
        await registrar_carteira(sessao, carteira, "custodiante/btg/carteira/x", COLETADO_EM)
        await sessao.commit()

    rodar_com_sessao(gravar)

    resposta = app_client.get(
        "/api/v1/carteiras", params={"fundo_cnpj": FUNDO, "data_referencia": DATA.isoformat()}
    )

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["fundo_cnpj"] == FUNDO
    assert corpo["posicoes"] == [
        {
            "classe": "titulo_publico",
            "identificador": "LTN2027",
            "descricao": "LTN 01/01/2027",
            "quantidade": "1000.00000000",
            "valor": "950000.00000000",
            "referencia_origem": "custodiante/btg/carteira/x",
        }
    ]


def test_cnpj_fora_do_formato_e_400(app_client: TestClient[Litestar]) -> None:
    resposta = app_client.get(
        "/api/v1/carteiras", params={"fundo_cnpj": "123", "data_referencia": DATA.isoformat()}
    )

    assert resposta.status_code == 400, resposta.text


def test_sem_token_e_401(app: Litestar) -> None:
    with TestClient(app=app) as cliente:
        resposta = cliente.get(
            "/api/v1/carteiras",
            params={"fundo_cnpj": FUNDO, "data_referencia": DATA.isoformat()},
        )

    assert resposta.status_code == 401, resposta.text
