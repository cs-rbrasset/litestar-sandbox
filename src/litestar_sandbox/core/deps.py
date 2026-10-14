from typing import TypeAlias

from advanced_alchemy.filters import FilterTypes
from litestar.di import NamedDependency
from litestar.params import SkipValidation

FilterDep: TypeAlias = NamedDependency[SkipValidation[list[FilterTypes]]]
