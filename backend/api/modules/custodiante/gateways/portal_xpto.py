"""[exemplo] Gateway de scraping — portal sem API, entrega HTML.

Scraping é só mais um gateway: mesma interface, mesma regra (não interpreta o conteúdo). O que
muda é o custo da falha — quando a coleta quebra, o HTML e o screenshot do momento do erro vão
pro storage em `{prefixo}/falhas/`, senão não tem como saber depois o que o portal mostrou.

Stub: falta o navegador (`_navegador.py`) e os termos de uso [AJUSTAR].
"""


from typing import TYPE_CHECKING

from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.protocols import ArquivoBruto, DocumentoIndisponivelError

if TYPE_CHECKING:
    import datetime


class GatewayPortalXpto:
    codigo = CodigoCustodiante.PORTAL_XPTO

    async def baixar_carteira(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        msg = "[AJUSTAR] gateway de scraping do portal_xpto ainda não implementado"
        raise NotImplementedError(msg)

    async def baixar_extrato(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        msg = f"{self.codigo} não fornece extrato"
        raise DocumentoIndisponivelError(msg)
