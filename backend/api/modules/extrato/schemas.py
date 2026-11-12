import datetime
import decimal

import msgspec


class LancamentoResposta(msgspec.Struct):
    documento: str
    tipo: str
    descricao: str
    valor: decimal.Decimal
    referencia_origem: str


class ExtratoResposta(msgspec.Struct):
    fundo_cnpj: str
    data_referencia: datetime.date
    lancamentos: list[LancamentoResposta]
