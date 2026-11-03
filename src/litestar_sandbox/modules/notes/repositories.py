from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from litestar_sandbox.modules.notes.models import Note


class NoteRepository(SQLAlchemyAsyncRepository[Note]):
    model_type = Note
