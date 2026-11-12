"""[exemplo] Parser do `portal_xpto` — HTML de tabela.

Stub, mas já no formato certo: função pura, sem I/O, levantando `LayoutNaoReconhecidoError`
quando o HTML não tem a forma esperada (e não um erro genérico, que o job trataria como falha
de coleta e repetiria à toa).
"""

from typing import TYPE_CHECKING

from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from modules.carteira.public import CarteiraNormalizada
    from modules.custodiante.protocols import ArquivoBruto


def parse_carteira(arquivos: Sequence[ArquivoBruto]) -> CarteiraNormalizada:
    htmls = [arquivo for arquivo in arquivos if arquivo.formato == "html"]
    if not htmls:
        msg = "esperado ao menos 1 HTML de carteira"
        raise LayoutNaoReconhecidoError(msg)
    msg = "[AJUSTAR] parser do portal_xpto ainda não implementado"
    raise NotImplementedError(msg)
