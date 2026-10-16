from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from litestar_sandbox.modules.trades.models import Trade


class TradeRepository(SQLAlchemyAsyncRepository[Trade]):
    model_type = Trade
