import datetime

from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from litestar_sandbox.modules.instruments.enums import InstrumentType


class Instrument(BigIntAuditBase):
    name: Mapped[str] = mapped_column(String(200), index=True)
    cetip_code: Mapped[str] = mapped_column(String(20), unique=True)
    instrument_type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType, native_enum=False, create_constraint=True, length=20)
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTimeUTC(timezone=True), default=None
    )
