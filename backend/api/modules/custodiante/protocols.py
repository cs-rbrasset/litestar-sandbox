"""Os contratos que todo custodiante novo tem que cumprir — e a fronteira entre I/O e parse.

**Gateway** faz I/O e nada mais: busca o arquivo e devolve bytes. Não interpreta conteúdo, não
sabe o que é uma posição. Scraping é só mais um gateway — entrega HTML em vez de XML.
Chama-se gateway, e não repository, exatamente porque não devolve objeto de domínio.

**Parser** é função pura: `list[ArquivoBruto]` → canônico. Sem classe e sem `Protocol` próprio
(não tem estado nem variação de comportamento a injetar), só um alias de tipo.

Separar os dois é o que permite **reprocessar**: com o bruto guardado, corrigir um parser ou
extrair um campo novo do histórico não precisa chamar o custodiante de novo.
"""

import dataclasses
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol, TypeAlias

from modules.carteira.public import CarteiraNormalizada
from modules.extrato.public import ExtratoNormalizado

if TYPE_CHECKING:
    import datetime

    from modules.custodiante.enums import CodigoCustodiante


@dataclasses.dataclass(frozen=True, slots=True)
class ArquivoBruto:
    """Exatamente o que o custodiante mandou, sem interpretação."""

    nome: str
    conteudo: bytes
    formato: str  # "xml", "html", "csv", "pdf"...


class GatewayCustodiante(Protocol):
    """Só I/O. Uma implementação por custodiante, em `gateways/`."""

    codigo: CodigoCustodiante

    async def baixar_carteira(
        self, fundo_cnpj: str, data: datetime.date
    ) -> list[ArquivoBruto]: ...

    async def baixar_extrato(
        self, fundo_cnpj: str, data: datetime.date
    ) -> list[ArquivoBruto]: ...


ParseCarteira: TypeAlias = Callable[[Sequence[ArquivoBruto]], CarteiraNormalizada]  # noqa: UP040
ParseExtrato: TypeAlias = Callable[[Sequence[ArquivoBruto]], ExtratoNormalizado]  # noqa: UP040


@dataclasses.dataclass(frozen=True, slots=True)
class Adaptador:
    """Gateway + os parsers dele. `None` = o custodiante não fornece aquele documento."""

    gateway: GatewayCustodiante
    parse_carteira: ParseCarteira | None = None
    parse_extrato: ParseExtrato | None = None


class DocumentoIndisponivelError(LookupError):
    """O custodiante não fornece esse documento — repetir não vai mudar isso."""


__all__ = (
    "Adaptador",
    "ArquivoBruto",
    "DocumentoIndisponivelError",
    "GatewayCustodiante",
    "ParseCarteira",
    "ParseExtrato",
)
