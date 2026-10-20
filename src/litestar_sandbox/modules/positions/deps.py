from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from litestar_sandbox.modules.positions.protocols import PositionServiceProtocol

PositionServiceDep: TypeAlias = NamedDependency[SkipValidation[PositionServiceProtocol]]
