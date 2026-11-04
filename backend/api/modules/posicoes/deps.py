from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from modules.posicoes.protocols import PositionServiceProtocol

PositionServiceDep: TypeAlias = NamedDependency[SkipValidation[PositionServiceProtocol]]
