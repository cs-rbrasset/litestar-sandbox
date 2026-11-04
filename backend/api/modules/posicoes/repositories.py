from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from modules.posicoes.models import PositionMovement


class PositionMovementRepository(SQLAlchemyAsyncRepository[PositionMovement]):
    model_type = PositionMovement
