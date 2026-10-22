from typing import TYPE_CHECKING, Any

from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from litestar_sandbox.core.identity import current_identity, current_trace_id

if TYPE_CHECKING:
    from litestar import Litestar
    from sqlalchemy.engine import Connection

    from litestar_sandbox.core.settings import DatabaseSettings


class MissingIdentityError(RuntimeError):
    """Transação aberta sem identidade: a trilha de auditoria ficaria sem autor."""


class IdentitySession(Session):
    """Sessão síncrona por baixo do AsyncSession da app; carrega o evento de identidade."""


@event.listens_for(IdentitySession, "after_begin")
def _push_identity(session: Session, transaction: Any, connection: Connection) -> None:
    """Empurra quem está agindo para o Postgres no início de cada transação.

    Num evento, e não num provider de dependência, porque não tem como ser esquecido. No
    SQLite (testes) não faz nada: SET ROLE não existe lá.
    """
    if connection.dialect.name != "postgresql":
        return
    identity = current_identity.get()
    if identity is None:
        # falha ruidosa: melhor a operação parar do que gravar trilha anônima
        msg = "transação sem identidade; use use_identity() fora de requests"
        raise MissingIdentityError(msg)
    connection.execute(text("select app.assumir_identidade(:role)"), {"role": identity.db_role})
    connection.execute(
        text("select set_config('app.trace_id', :trace_id, true)"),
        {"trace_id": current_trace_id.get() or ""},
    )


def create_sqlalchemy_config(database_settings: DatabaseSettings) -> SQLAlchemyAsyncConfig:
    session_class = IdentitySession if database_settings.assume_identity else Session
    return SQLAlchemyAsyncConfig(
        connection_string=database_settings.database_url,
        session_config=AsyncSessionConfig(sync_session_class=session_class),
        before_send_handler="autocommit",
        create_all=True,
    )


def create_sqlalchemy_plugin(config: SQLAlchemyAsyncConfig) -> SQLAlchemyPlugin:
    return SQLAlchemyPlugin(config)


def get_sqlalchemy_config(app: Litestar) -> SQLAlchemyAsyncConfig:
    """Config do plugin registrado no app, para código que roda fora do request."""
    config = app.plugins.get(SQLAlchemyPlugin).config[0]
    if not isinstance(config, SQLAlchemyAsyncConfig):
        msg = "SQLAlchemyPlugin sem config assíncrona"
        raise TypeError(msg)
    return config
