"""Sessão de navegador compartilhada pelos gateways de scraping.

[AJUSTAR: termos de uso para scraping de portais] — antes de ligar qualquer gateway destes num
portal real, confirmar que os termos de uso do custodiante permitem acesso automatizado.

Fica num arquivo próprio porque subir um navegador é caro: um gateway de scraping pede a
sessão daqui em vez de abrir a própria. Continua sendo só I/O — devolve HTML, nunca domínio.

Stub: a dependência de navegação (Playwright) ainda não está no `pyproject.toml`; entra junto
com o primeiro gateway de scraping de verdade.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


class SessaoNavegador:
    """Contrato pretendido; a implementação entra com o primeiro portal real."""

    async def __aenter__(self) -> SessaoNavegador:
        msg = "[AJUSTAR] sessão de navegador (Playwright) ainda não implementada"
        raise NotImplementedError(msg)

    async def __aexit__(
        self,
        tipo: type[BaseException] | None,
        erro: BaseException | None,
        traco: TracebackType | None,
    ) -> None:
        return None

    async def abrir(self, url: str) -> str:
        """Devolve o HTML da página. Falha de coleta aqui **pode** ser repetida pelo job."""
        raise NotImplementedError
