from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from modules.notes.models import Note


class NoteRepository(SQLAlchemyAsyncRepository[Note]):
    model_type = Note
