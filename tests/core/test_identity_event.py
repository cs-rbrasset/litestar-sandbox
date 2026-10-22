"""O evento after_begin que empurra a identidade para o Postgres.

Os testes não precisam de Postgres: chamam o handler com uma conexão falsa que registra o
SQL. O que eles provam é a regra; o SET ROLE de verdade precisa de um teste contra Postgres.
"""

import dataclasses
from typing import Any

import pytest
from sqlalchemy.orm import Session

from litestar_sandbox.core.database import (
    IdentitySession,
    MissingIdentityError,
    _push_identity,
    create_sqlalchemy_config,
)
from litestar_sandbox.core.identity import SYSTEM, Identity, current_identity, use_identity
from litestar_sandbox.core.settings import DatabaseSettings


@dataclasses.dataclass
class FakeDialect:
    name: str


@dataclasses.dataclass
class FakeConnection:
    dialect: FakeDialect
    executed: list[tuple[str, dict[str, Any]]] = dataclasses.field(default_factory=list)

    def execute(self, statement: Any, params: dict[str, Any]) -> None:
        self.executed.append((str(statement), params))


def test_sqlite_is_untouched_even_without_identity() -> None:
    connection = FakeConnection(FakeDialect("sqlite"))
    _push_identity(None, None, connection)  # type: ignore[arg-type]
    assert connection.executed == []


def test_postgres_without_identity_fails_loudly() -> None:
    with pytest.raises(MissingIdentityError):
        _push_identity(None, None, FakeConnection(FakeDialect("postgresql")))  # type: ignore[arg-type]


def test_postgres_assumes_role_and_sets_trace_id() -> None:
    connection = FakeConnection(FakeDialect("postgresql"))
    alice = Identity(subject="u_alice", db_role="u_alice", name="Alice")
    with use_identity(alice, trace_id="req-1"):
        _push_identity(None, None, connection)  # type: ignore[arg-type]
    assert connection.executed == [
        ("select app.assumir_identidade(:role)", {"role": "u_alice"}),
        ("select set_config('app.trace_id', :trace_id, true)", {"trace_id": "req-1"}),
    ]


@pytest.mark.parametrize(("enabled", "expected"), [(True, IdentitySession), (False, Session)])
def test_identity_event_is_opt_in(enabled: bool, expected: type[Session]) -> None:
    settings = DatabaseSettings(database_url="sqlite+aiosqlite://", assume_identity=enabled)
    config = create_sqlalchemy_config(settings)
    assert config.session_config.sync_session_class is expected


def test_use_identity_restores_previous_context() -> None:
    alice = Identity(subject="u_alice", db_role="u_alice", name="Alice")
    with use_identity(alice):
        with use_identity(SYSTEM):
            assert current_identity.get() is SYSTEM
        assert current_identity.get() is alice
    assert current_identity.get() is None
