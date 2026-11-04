from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from modules.instruments.models import Instrument


class InstrumentRepository(SQLAlchemyAsyncRepository[Instrument]):
    model_type = Instrument
