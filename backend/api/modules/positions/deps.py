from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from modules.positions.protocols import PositionServiceProtocol

PositionServiceDep: TypeAlias = NamedDependency[SkipValidation[PositionServiceProtocol]]
