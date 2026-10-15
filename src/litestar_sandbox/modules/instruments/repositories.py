from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from litestar_sandbox.modules.instruments.models import Instrument


class InstrumentRepository(SQLAlchemyAsyncRepository[Instrument]):
    model_type = Instrument
