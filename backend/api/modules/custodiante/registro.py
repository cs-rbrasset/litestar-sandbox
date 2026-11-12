"""`CodigoCustodiante` → `Adaptador`. É aqui que um custodiante novo passa a existir.

Custodiante novo = um gateway em `gateways/`, um parser em `parsers/`, uma fixture no teste e
**uma linha aqui**. Nada mais no sistema precisa saber que ele existe.

As entradas são fábricas (e não adaptadores prontos) porque o gateway lê credencial do
ambiente: montar tudo no import quebraria qualquer processo que não tenha todas as credenciais
— inclusive os testes.
"""

from typing import TYPE_CHECKING

from core.settings import CustodianteSettings
from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.gateways.btg import GatewayBtg
from modules.custodiante.gateways.portal_xpto import GatewayPortalXpto
from modules.custodiante.parsers import btg as parser_btg
from modules.custodiante.parsers import portal_xpto as parser_portal_xpto
from modules.custodiante.protocols import Adaptador

if TYPE_CHECKING:
    from collections.abc import Callable


class CustodianteDesconhecidoError(LookupError):
    """Código sem entrada no registro."""


REGISTRO: dict[CodigoCustodiante, Callable[[], Adaptador]] = {
    CodigoCustodiante.BTG: lambda: Adaptador(
        gateway=GatewayBtg(CustodianteSettings.from_env(CodigoCustodiante.BTG.value)),
        parse_carteira=parser_btg.parse_carteira,
        parse_extrato=None,  # este custodiante não fornece extrato
    ),
    CodigoCustodiante.PORTAL_XPTO: lambda: Adaptador(
        gateway=GatewayPortalXpto(),
        parse_carteira=parser_portal_xpto.parse_carteira,
        parse_extrato=None,
    ),
}


def registrado(codigo: CodigoCustodiante) -> bool:
    """Checa a existência sem montar o gateway — não exige credencial no ambiente."""
    return codigo in REGISTRO


def adaptador(codigo: CodigoCustodiante) -> Adaptador:
    try:
        criar = REGISTRO[codigo]
    except KeyError as erro:
        raise CustodianteDesconhecidoError(codigo) from erro
    # a fábrica roda fora do try de propósito: um KeyError de variável de ambiente ausente
    # não pode ser confundido com "custodiante desconhecido".
    return criar()


__all__ = ("REGISTRO", "CustodianteDesconhecidoError", "adaptador", "registrado")
