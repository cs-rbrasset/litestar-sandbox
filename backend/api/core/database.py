from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.identity import current_identity, current_trace_id

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar import Litestar
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session

    from core.settings import DatabaseSettings


class MissingIdentityError(RuntimeError):
    """Transação aberta sem identidade: a trilha de auditoria ficaria sem autor."""


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


class IdentityAsyncConfig(SQLAlchemyAsyncConfig):
    """Config que registra o evento de identidade nas sessões da app.

    O evento vai no sessionmaker síncrono que o advanced-alchemy cria por baixo do
    async_sessionmaker. Passar sync_session_class no session_config não funciona: o
    advanced-alchemy sobrescreve esse parâmetro com o próprio sessionmaker, em silêncio.
    """

    def create_session_maker(self) -> Callable[[], AsyncSession]:
        maker = super().create_session_maker()
        if isinstance(maker, async_sessionmaker):
            sync_maker = maker.kw["sync_session_class"]
            if not event.contains(sync_maker, "after_begin", _push_identity):
                event.listen(sync_maker, "after_begin", _push_identity)
        return maker


def create_sqlalchemy_config(database_settings: DatabaseSettings) -> SQLAlchemyAsyncConfig:
    config_class = (
        IdentityAsyncConfig if database_settings.assume_identity else SQLAlchemyAsyncConfig
    )
    return config_class(
        connection_string=database_settings.database_url,
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
