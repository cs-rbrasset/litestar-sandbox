from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from modules.trades.models import Trade


class TradeRepository(SQLAlchemyAsyncRepository[Trade]):
    model_type = Trade
