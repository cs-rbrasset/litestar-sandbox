from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from core.deps import SessionDep
from modules.carteira.protocols import CarteiraServiceProtocol
from modules.carteira.services import CarteiraService

CarteiraServiceDep: TypeAlias = NamedDependency[SkipValidation[CarteiraServiceProtocol]]


async def provide_carteira_service(db_session: SessionDep) -> CarteiraServiceProtocol:
    return CarteiraService(db_session)
