from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from litestar_sandbox.modules.positions.models import PositionMovement


class PositionMovementRepository(SQLAlchemyAsyncRepository[PositionMovement]):
    model_type = PositionMovement
