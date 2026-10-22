"""O evento after_begin que empurra a identidade para o Postgres.

Os testes não precisam de Postgres: chamam o handler com uma conexão falsa que registra o
SQL. O que eles provam é a regra; o SET ROLE de verdade precisa de um teste contra Postgres.
"""

import dataclasses
from typing import Any, cast

import pytest

from litestar_sandbox.core.database import (
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


def push(connection: FakeConnection) -> None:
    _push_identity(cast("Any", None), cast("Any", None), cast("Any", connection))


def test_sqlite_is_untouched_even_without_identity() -> None:
    connection = FakeConnection(FakeDialect("sqlite"))
    push(connection)
    assert connection.executed == []


def test_postgres_without_identity_fails_loudly() -> None:
    with pytest.raises(MissingIdentityError):
        push(FakeConnection(FakeDialect("postgresql")))


def test_postgres_assumes_role_and_sets_trace_id() -> None:
    connection = FakeConnection(FakeDialect("postgresql"))
    alice = Identity(subject="u_alice", db_role="u_alice", name="Alice")
    with use_identity(alice, trace_id="req-1"):
        push(connection)
    assert connection.executed == [
        ("select app.assumir_identidade(:role)", {"role": "u_alice"}),
        ("select set_config('app.trace_id', :trace_id, true)", {"trace_id": "req-1"}),
    ]


def session_listeners(*, assume_identity: bool, makers: int = 1) -> list[str]:
    """Os listeners de after_begin na sessão que a config realmente cria."""
    settings = DatabaseSettings(database_url="sqlite+aiosqlite://", assume_identity=assume_identity)
    config = create_sqlalchemy_config(settings)
    for _ in range(makers - 1):
        config.create_session_maker()
    session = config.create_session_maker()()
    dispatch: Any = session.sync_session.dispatch  # os atributos de evento são dinâmicos
    return [listener.__name__ for listener in dispatch.after_begin]


@pytest.mark.parametrize(("enabled", "expected"), [(True, ["_push_identity"]), (False, [])])
def test_identity_event_reaches_real_sessions_only_when_enabled(
    enabled: bool, expected: list[str]
) -> None:
    """Confere a sessão criada de fato, e não um parâmetro de configuração.

    Foi um parâmetro (sync_session_class) que enganou a primeira versão: o advanced-alchemy
    o descartava em silêncio, e o evento nunca disparava.
    """
    assert session_listeners(assume_identity=enabled) == expected


def test_identity_event_is_registered_once() -> None:
    assert session_listeners(assume_identity=True, makers=3) == ["_push_identity"]


def test_use_identity_restores_previous_context() -> None:
    alice = Identity(subject="u_alice", db_role="u_alice", name="Alice")
    with use_identity(alice):
        with use_identity(SYSTEM):
            assert current_identity.get() is SYSTEM
        assert current_identity.get() is alice
    assert current_identity.get() is None
