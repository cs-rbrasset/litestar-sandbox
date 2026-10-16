import datetime
import decimal

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import Date, Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from litestar_sandbox.modules.trades.enums import TradeSide, TradeStatus


class Trade(BigIntAuditBase):
    fund_cnpj: Mapped[str] = mapped_column(String(14), index=True)
    instrument_id: Mapped[int] = mapped_column(Integer, index=True)
    cetip_code: Mapped[str] = mapped_column(String(20))
    trade_date: Mapped[datetime.date] = mapped_column(Date)
    side: Mapped[TradeSide] = mapped_column(
        Enum(TradeSide, native_enum=False, create_constraint=True, length=20)
    )
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(20, 8))
    status: Mapped[TradeStatus] = mapped_column(
        Enum(TradeStatus, native_enum=False, create_constraint=True, length=20),
        default=TradeStatus.PENDING,
    )
