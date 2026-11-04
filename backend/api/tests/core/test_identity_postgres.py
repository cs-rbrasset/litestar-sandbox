"""A identidade chegando de verdade ao Postgres, pela sessão da app.

Roda só com TEST_DATABASE_URL apontando para um Postgres onde o db/identity.sql foi aplicado
(por exemplo, o Supabase de testes). Sem ela, os testes são pulados: o SQLite não tem SET ROLE.
"""

import asyncio
import os
import sys
from typing import Any

import pytest
from sqlalchemy import text

from core.database import MissingIdentityError, create_sqlalchemy_config
from core.identity import SYSTEM, Identity, use_identity
from core.settings import DatabaseSettings

POSTGRES_URL = os.getenv("TEST_DATABASE_URL", "")

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(
        not POSTGRES_URL.startswith("postgresql"), reason="precisa de TEST_DATABASE_URL (Postgres)"
    ),
]

ALICE = Identity(subject="u_alice", db_role="u_alice", name="Alice")


@pytest.fixture
def anyio_backend() -> tuple[str, dict[str, Any]]:
    # o psycopg assíncrono não roda no ProactorEventLoop, o padrão do asyncio no Windows
    if sys.platform == "win32":
        return "asyncio", {"loop_factory": asyncio.SelectorEventLoop}
    return "asyncio", {}


@pytest.fixture
def config():
    return create_sqlalchemy_config(
        DatabaseSettings(database_url=POSTGRES_URL, assume_identity=True)
    )


async def whoami(config) -> tuple[str, str, str]:
    async with config.get_session() as session:
        row = (
            await session.execute(
                text("select current_user, session_user, current_setting('app.trace_id', true)")
            )
        ).one()
        await session.rollback()
    return tuple(row)


async def test_transaction_runs_as_the_request_identity(config) -> None:
    with use_identity(ALICE, trace_id="req-pg-1"):
        current, session_user, trace_id = await whoami(config)
    assert current == "u_alice"
    assert session_user != "u_alice"  # a conexão continua sendo a da app
    assert trace_id == "req-pg-1"


async def test_system_identity_for_background_work(config) -> None:
    with use_identity(SYSTEM):
        current, _, _ = await whoami(config)
    assert current == "app_sistema"


async def test_transaction_without_identity_is_refused(config) -> None:
    with pytest.raises(MissingIdentityError):
        await whoami(config)


async def test_unknown_role_is_refused_by_the_database(config) -> None:
    ghost = Identity(subject="u_ninguem", db_role="u_ninguem", name="Ninguém")
    with use_identity(ghost), pytest.raises(Exception, match="u_ninguem"):
        await whoami(config)
