import datetime
import decimal

from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Product(BigIntAuditBase):
    name: Mapped[str] = mapped_column(String(200), index=True)
    sku: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2))
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTimeUTC(True), default=None)
