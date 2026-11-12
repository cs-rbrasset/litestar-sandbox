"""O registro é a única lista de custodiantes do sistema — aqui ela é conferida.

Custodiante novo = gateway + parser + fixture + **uma linha no registro**. Se a linha faltar, é
aqui que aparece, não em runtime no meio de uma importação.
"""

import pytest

from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.registro import REGISTRO


def test_todo_codigo_tem_entrada_no_registro() -> None:
    assert set(REGISTRO) == set(CodigoCustodiante)


@pytest.mark.parametrize("codigo", list(CodigoCustodiante))
def test_entrada_declara_ao_menos_um_parser(
    codigo: CodigoCustodiante, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Custodiante sem parser nenhum não tem como entregar documento — é erro de cadastro."""
    monkeypatch.setenv(f"CUSTODIANTE_{codigo.value.upper()}_URL", "https://exemplo.invalido")
    monkeypatch.setenv(f"CUSTODIANTE_{codigo.value.upper()}_TOKEN", "token-de-teste")

    adaptado = REGISTRO[codigo]()

    assert adaptado.gateway.codigo is codigo
    assert adaptado.parse_carteira is not None or adaptado.parse_extrato is not None
