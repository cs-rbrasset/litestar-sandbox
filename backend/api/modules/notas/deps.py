from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from modules.notas.protocols import NoteServiceProtocol

NoteServiceDep: TypeAlias = NamedDependency[SkipValidation[NoteServiceProtocol]]
