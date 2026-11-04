from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from modules.notes.protocols import NoteServiceProtocol

NoteServiceDep: TypeAlias = NamedDependency[SkipValidation[NoteServiceProtocol]]
