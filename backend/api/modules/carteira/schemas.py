import datetime
import decimal
from typing import Annotated, TypeAlias

import msgspec

FundoCnpj: TypeAlias = Annotated[str, msgspec.Meta(pattern=r"^\d{14}$")]  # noqa: UP040


class PosicaoResposta(msgspec.Struct):
    classe: str
    identificador: str
    descricao: str
    quantidade: decimal.Decimal
    valor: decimal.Decimal
    referencia_origem: str


class CarteiraResposta(msgspec.Struct):
    fundo_cnpj: str
    data_referencia: datetime.date
    posicoes: list[PosicaoResposta]
