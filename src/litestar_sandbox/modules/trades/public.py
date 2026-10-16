import datetime
import decimal

import msgspec

from litestar_sandbox.modules.trades.enums import TradeSide

TRADE_SETTLED = "trades.trade_settled"


class TradeSettled(msgspec.Struct, frozen=True):
    trade_id: int
    fund_cnpj: str
    instrument_id: int
    cetip_code: str
    trade_date: datetime.date
    side: TradeSide
    quantity: int
    unit_price: decimal.Decimal


__all__ = ("TRADE_SETTLED", "TradeSettled", "TradeSide")
