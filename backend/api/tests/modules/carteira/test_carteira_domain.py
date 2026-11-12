"""Domínio da carteira: testado sem banco, sem app, sem fixture de infraestrutura.

É exatamente isso que o contrato de pureza do import-linter protege — se alguém encostar
sqlalchemy no `domain/`, este arquivo passa a precisar de banco pra rodar.
"""

import datetime
import decimal

import pytest

from modules.carteira.domain import (
    CarteiraInvalidaError,
    CarteiraNormalizada,
    ClasseAtivo,
    PosicaoNormalizada,
    validar,
)

DATA = datetime.date(2026, 10, 31)


def _posicao(identificador: str = "LTN2027", classe: ClasseAtivo = ClasseAtivo.TITULO_PUBLICO):
    return PosicaoNormalizada(
        classe=classe,
        identificador=identificador,
        quantidade=decimal.Decimal("100"),
        valor=decimal.Decimal("95000.00"),
    )


def test_carteira_valida_passa() -> None:
    carteira = CarteiraNormalizada(
        fundo_cnpj="12345678000190", data_referencia=DATA, posicoes=(_posicao(),)
    )

    validar(carteira)  # não levanta


def test_cnpj_fora_do_formato_e_invalido() -> None:
    carteira = CarteiraNormalizada(
        fundo_cnpj="123", data_referencia=DATA, posicoes=(_posicao(),)
    )

    with pytest.raises(CarteiraInvalidaError, match="fundo_cnpj"):
        validar(carteira)


def test_carteira_sem_posicao_e_invalida() -> None:
    carteira = CarteiraNormalizada(
        fundo_cnpj="12345678000190", data_referencia=DATA, posicoes=()
    )

    with pytest.raises(CarteiraInvalidaError, match="sem posições"):
        validar(carteira)


def test_posicao_repetida_na_mesma_carteira_e_invalida() -> None:
    carteira = CarteiraNormalizada(
        fundo_cnpj="12345678000190",
        data_referencia=DATA,
        posicoes=(_posicao(), _posicao()),
    )

    with pytest.raises(CarteiraInvalidaError, match="repetidas"):
        validar(carteira)


def test_mesmo_identificador_em_classes_diferentes_e_valido() -> None:
    """A chave de negócio inclui a classe: o mesmo código pode aparecer em duas seções."""
    carteira = CarteiraNormalizada(
        fundo_cnpj="12345678000190",
        data_referencia=DATA,
        posicoes=(_posicao(), _posicao(classe=ClasseAtivo.COMPROMISSADA)),
    )

    validar(carteira)


def test_soma_das_posicoes_nao_e_conferida_contra_o_pl() -> None:
    """[AJUSTAR: regras de validação] — "soma = PL" está errado: o PL inclui caixa, provisões,
    valores a pagar e a receber. Este teste trava a ausência da regra de propósito, pra ninguém
    "consertar" isso sem falar com quem entende de carteira de fundos.
    """
    carteira = CarteiraNormalizada(
        fundo_cnpj="12345678000190",
        data_referencia=DATA,
        posicoes=(_posicao(),),
        patrimonio_liquido=decimal.Decimal("1.00"),
    )

    validar(carteira)  # não levanta, mesmo com PL que não bate com a soma
