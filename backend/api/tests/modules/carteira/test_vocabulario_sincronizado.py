"""O vocabulário do canônico e o CHECK da tabela são duas cópias — aqui elas são comparadas.

Por que duas cópias: `database` não pode importar `backend/api` (pacote publicável à parte) e o
`domain/` não pode importar `database` (regra de pureza). A saída foi copiar e travar a cópia
com teste, em vez de abrir uma das duas regras.
"""

from database.models.carteira.enums import CLASSES_ATIVO
from database.models.extrato.enums import TIPOS_LANCAMENTO

from modules.carteira.domain import ClasseAtivo
from modules.extrato.domain import TipoLancamento


def test_classes_de_ativo_batem_com_o_check_da_tabela() -> None:
    assert sorted(classe.value for classe in ClasseAtivo) == sorted(CLASSES_ATIVO)


def test_tipos_de_lancamento_batem_com_o_check_da_tabela() -> None:
    assert sorted(tipo.value for tipo in TipoLancamento) == sorted(TIPOS_LANCAMENTO)
