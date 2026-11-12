from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import datetime

    from modules.extrato.models import LancamentoExtrato


class ExtratoServiceProtocol(Protocol):
    async def lancamentos_em(
        self, fundo_cnpj: str, data_referencia: datetime.date
    ) -> list[LancamentoExtrato]: ...
