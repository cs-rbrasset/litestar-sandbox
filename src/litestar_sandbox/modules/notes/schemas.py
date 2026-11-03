import datetime
from typing import Any

import msgspec


class NoteCreate(msgspec.Struct):
    title: str = "Sem título"


class NoteUpdate(msgspec.Struct):
    title: str
    content: dict[str, Any]
    published: bool = False


class NoteRead(msgspec.Struct):
    id: int
    title: str
    content: dict[str, Any]
    published: bool = False
    updated_at: datetime.datetime | None = None


class NoteSummary(msgspec.Struct):
    id: int
    title: str
    published: bool
    updated_at: datetime.datetime | None = None


class WikiEntry(msgspec.Struct):
    id: int
    title: str
    author_name: str
    content: dict[str, Any]
    updated_at: datetime.datetime | None = None
