from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import datetime

    from modules.carteira.models import PosicaoCarteira


class CarteiraServiceProtocol(Protocol):
    async def posicoes_em(
        self, fundo_cnpj: str, data_referencia: datetime.date
    ) -> list[PosicaoCarteira]: ...
