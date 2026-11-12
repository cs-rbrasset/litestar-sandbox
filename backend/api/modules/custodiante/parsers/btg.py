"""[exemplo] Parser do custodiante `btg` — XML no layout ANBIMA.

Função pura: recebe o que o gateway baixou e devolve o canônico. Nunca faz I/O, nem para
"buscar o arquivo que faltou" — se faltou, é erro de layout e o job não repete.
"""

from typing import TYPE_CHECKING

from modules.custodiante.parsers.anbima_xml import ler_carteira
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from modules.carteira.public import CarteiraNormalizada
    from modules.custodiante.protocols import ArquivoBruto


def parse_carteira(arquivos: Sequence[ArquivoBruto]) -> CarteiraNormalizada:
    xmls = [arquivo for arquivo in arquivos if arquivo.formato == "xml"]
    if len(xmls) != 1:
        msg = f"esperado exatamente 1 XML de carteira, veio {len(xmls)}"
        raise LayoutNaoReconhecidoError(msg)
    return ler_carteira(xmls[0].conteudo)
