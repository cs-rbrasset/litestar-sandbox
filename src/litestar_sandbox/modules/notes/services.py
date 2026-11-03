from typing import TYPE_CHECKING, Any

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from litestar.exceptions import NotFoundException

from litestar_sandbox.modules.notes.models import Note
from litestar_sandbox.modules.notes.repositories import NoteRepository

if TYPE_CHECKING:
    from collections.abc import Sequence


class NoteService(SQLAlchemyAsyncRepositoryService[Note, NoteRepository]):
    repository_type = NoteRepository

    async def create_for_owner(self, owner: str, author_name: str, title: str) -> Note:
        return await self.create(
            {"owner": owner, "author_name": author_name, "title": title, "content": {}}
        )

    async def list_for_owner(self, owner: str) -> Sequence[Note]:
        return await self.get_many(Note.owner == owner)

    async def get_owned(self, note_id: int, owner: str) -> Note:
        note = await self.get_one_or_none(id=note_id, owner=owner)
        if note is None:
            msg = f"note {note_id} not found"
            raise NotFoundException(detail=msg)
        return note

    async def update_owned(
        self, note_id: int, owner: str, title: str, content: dict[str, Any], published: bool
    ) -> Note:
        # 404 em vez de atualizar: dono errado não deve nem saber se o artigo existe.
        await self.get_owned(note_id, owner)
        return await self.update(
            {"title": title, "content": content, "published": published}, item_id=note_id
        )

    async def list_published(self) -> Sequence[Note]:
        return await self.get_many(Note.published.is_(True))

    async def delete_owned(self, note_id: int, owner: str) -> None:
        # 404 em vez de apagar: dono errado não deve nem saber se o artigo existe.
        await self.get_owned(note_id, owner)
        await self.delete(note_id)
