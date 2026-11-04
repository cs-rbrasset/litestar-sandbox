from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from modules.ativos.models import Instrument


class InstrumentRepository(SQLAlchemyAsyncRepository[Instrument]):
    model_type = Instrument
