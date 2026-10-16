import datetime
import decimal
from typing import Annotated, TypeAlias

import msgspec

from litestar_sandbox.modules.trades.enums import TradeSide

FundCnpj: TypeAlias = Annotated[str, msgspec.Meta(pattern=r"^\d{14}$")]  # noqa: UP040
PosInteger: TypeAlias = Annotated[int, msgspec.Meta(gt=0)]  # noqa: UP040


class TradeCreate(msgspec.Struct):
    fund_cnpj: FundCnpj
    instrument_id: PosInteger
    trade_date: datetime.date
    side: TradeSide
    quantity: PosInteger
    unit_price: decimal.Decimal

    def __post_init__(self):
        if self.unit_price <= 0:
            raise ValueError("unit_price deve ser maior que zero")
