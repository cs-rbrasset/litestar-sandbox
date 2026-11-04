import datetime
import decimal

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class PositionMovement(BigIntAuditBase):
    trade_id: Mapped[int] = mapped_column(Integer, unique=True)
    fund_cnpj: Mapped[str] = mapped_column(String(14), index=True)
    instrument_id: Mapped[int] = mapped_column(Integer, index=True)
    cetip_code: Mapped[str] = mapped_column(String(20))
    movement_date: Mapped[datetime.date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(20, 8))
