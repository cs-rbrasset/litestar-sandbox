"""Quem está agindo na requisição (ou no job) corrente.

O middleware de autenticação grava a identidade num ContextVar, e o evento da sessão do
SQLAlchemy (core/database.py) a empurra para o Postgres com SET LOCAL ROLE. Código que roda
fora de request (listeners, jobs) declara de propósito em nome de quem age, com use_identity().
"""

import contextlib
import dataclasses
import re
from contextvars import ContextVar
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Generator

# u_<object id do Entra> para pessoas; app_* para identidades técnicas (handoff do banco, seção 3).
# Só minúsculas, dígitos, _ e -: nada que precise de aspas num SET ROLE.
DB_ROLE_PATTERN = re.compile(r"^(u_[0-9a-z-]{1,64}|app_[a-z_]{1,32})$")


@dataclasses.dataclass(frozen=True)
class Identity:
    subject: str
    db_role: str
    name: str
    kind: Literal["user", "system"] = "user"

    def __post_init__(self) -> None:
        # o nome da role vai para um SET ROLE: só formatos conhecidos, nunca texto livre
        if not DB_ROLE_PATTERN.fullmatch(self.db_role):
            msg = f"db_role inválida: {self.db_role!r}"
            raise ValueError(msg)


SYSTEM = Identity(subject="system", db_role="app_sistema", name="Sistema", kind="system")

current_identity: ContextVar[Identity | None] = ContextVar("current_identity", default=None)
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)


@contextlib.contextmanager
def use_identity(identity: Identity, trace_id: str | None = None) -> Generator[Identity]:
    """Age como `identity` dentro do bloco e restaura o contexto anterior ao sair."""
    identity_token = current_identity.set(identity)
    trace_token = current_trace_id.set(trace_id)
    try:
        yield identity
    finally:
        current_trace_id.reset(trace_token)
        current_identity.reset(identity_token)
