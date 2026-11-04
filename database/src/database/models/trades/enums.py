import enum


class TradeSide(enum.StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(enum.StrEnum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
