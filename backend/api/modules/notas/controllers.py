from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, delete, get, post, put
from litestar.di import Provide
from litestar.params import FromPath

from modules.notas.deps import NoteServiceDep
from modules.notas.schemas import (
    NoteCreate,
    NoteRead,
    NoteSummary,
    NoteUpdate,
    WikiEntry,
)
from modules.notas.services import NoteService

if TYPE_CHECKING:
    from modules.notas.models import Note


def _owner(request: Request) -> str:
    # request.user é o Principal[Identity] que o SecurityPlugin resolveu (core/security.py);
    # db_role já é único por pessoa e validado (DB_ROLE_PATTERN), serve como dono do artigo.
    return request.user.user.db_role


def _to_read(note: Note) -> NoteRead:
    return NoteRead(
        id=note.id,
        title=note.title,
        content=note.content,
        published=note.published,
        updated_at=note.updated_at,
    )


class NotesController(Controller):
    path = "/notas"
    dependencies = {"note_service": Provide(create_service_provider(NoteService))}

    @get("/mine")
    async def list_my_notes(
        self, note_service: NoteServiceDep, request: Request
    ) -> list[NoteSummary]:
        notes = await note_service.list_for_owner(_owner(request))
        return [
            NoteSummary(id=n.id, title=n.title, published=n.published, updated_at=n.updated_at)
            for n in notes
        ]

    @post()
    async def create_note(
        self, note_service: NoteServiceDep, request: Request, data: NoteCreate
    ) -> NoteRead:
        note = await note_service.create_for_owner(
            _owner(request), request.user.user.name, data.title
        )
        return _to_read(note)

    @get("/wiki")
    async def list_wiki_entries(self, note_service: NoteServiceDep) -> list[WikiEntry]:
        notes = await note_service.list_published()
        return [
            WikiEntry(
                id=n.id, title=n.title, author_name=n.author_name, content=n.content,
                updated_at=n.updated_at,
            )
            for n in notes
        ]

    @get("/{note_id:int}")
    async def get_note(
        self, note_service: NoteServiceDep, request: Request, note_id: FromPath[int]
    ) -> NoteRead:
        note = await note_service.get_owned(note_id, _owner(request))
        return _to_read(note)

    @put("/{note_id:int}")
    async def update_note(
        self,
        note_service: NoteServiceDep,
        request: Request,
        note_id: FromPath[int],
        data: NoteUpdate,
    ) -> NoteRead:
        note = await note_service.update_owned(
            note_id, _owner(request), data.title, data.content, data.published
        )
        return _to_read(note)

    @delete("/{note_id:int}")
    async def delete_note(
        self, note_service: NoteServiceDep, request: Request, note_id: FromPath[int]
    ) -> None:
        await note_service.delete_owned(note_id, _owner(request))
