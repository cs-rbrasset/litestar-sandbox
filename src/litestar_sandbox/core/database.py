from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin

if TYPE_CHECKING:
    from litestar import Litestar

    from litestar_sandbox.core.settings import DatabaseSettings


def create_sqlalchemy_config(database_settings: DatabaseSettings) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
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
