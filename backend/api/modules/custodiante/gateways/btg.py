"""[exemplo] Gateway do custodiante `btg` — API que devolve XML.

Só I/O: autentica, baixa, devolve bytes. Não abre o XML, não valida campo, não sabe o que é
uma posição — quem interpreta é `parsers/btg.py`. Se amanhã o custodiante trocar de API, muda
só este arquivo; se trocar o layout do arquivo, muda só o parser.
"""

from typing import TYPE_CHECKING

import niquests

from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.protocols import ArquivoBruto, DocumentoIndisponivelError

if TYPE_CHECKING:
    import datetime

    from core.settings import CustodianteSettings

_TIMEOUT = 60.0


class GatewayBtg:
    codigo = CodigoCustodiante.BTG

    def __init__(self, settings: CustodianteSettings) -> None:
        self._settings = settings

    async def baixar_carteira(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        conteudo = await self._baixar("carteira", fundo_cnpj, data)
        return [
            ArquivoBruto(
                nome=f"carteira_{fundo_cnpj}_{data:%Y%m%d}.xml", conteudo=conteudo, formato="xml"
            )
        ]

    async def baixar_extrato(self, fundo_cnpj: str, data: datetime.date) -> list[ArquivoBruto]:
        """[exemplo] Este custodiante não fornece extrato — o `Adaptador` tem `parse_extrato=None`."""
        msg = f"{self.codigo} não fornece extrato"
        raise DocumentoIndisponivelError(msg)

    async def _baixar(self, documento: str, fundo_cnpj: str, data: datetime.date) -> bytes:
        url = f"{self._settings.url_base}/{documento}"
        parametros = {"cnpj": fundo_cnpj, "data": data.isoformat()}
        cabecalhos = {"Authorization": f"Bearer {self._settings.token}"}
        async with niquests.AsyncSession(timeout=_TIMEOUT) as sessao:
            resposta = await sessao.get(url, params=parametros, headers=cabecalhos)
            resposta.raise_for_status()
            return resposta.content or b""
