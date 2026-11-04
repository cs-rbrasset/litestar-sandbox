from typing import TypeAlias

from advanced_alchemy.filters import FilterTypes
from litestar.di import NamedDependency
from litestar.params import SkipValidation
from sqlalchemy.ext.asyncio import AsyncSession

FilterDep: TypeAlias = NamedDependency[SkipValidation[list[FilterTypes]]]
SessionDep: TypeAlias = NamedDependency[SkipValidation[AsyncSession]]
