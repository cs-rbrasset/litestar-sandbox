from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from core.deps import SessionDep
from modules.extrato.protocols import ExtratoServiceProtocol
from modules.extrato.services import ExtratoService

ExtratoServiceDep: TypeAlias = NamedDependency[SkipValidation[ExtratoServiceProtocol]]


async def provide_extrato_service(db_session: SessionDep) -> ExtratoServiceProtocol:
    return ExtratoService(db_session)
