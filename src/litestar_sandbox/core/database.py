from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin

if TYPE_CHECKING:
    from litestar_sandbox.core.settings import DatabaseSettings


def create_sqlalchemy_config(database_settings: DatabaseSettings) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        connection_string=database_settings.database_url,
        before_send_handler="autocommit",
        create_all=True,
    )


def create_sqlalchemy_plugin(config: SQLAlchemyAsyncConfig) -> SQLAlchemyPlugin:
    return SQLAlchemyPlugin(config)
