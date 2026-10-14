from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin

if TYPE_CHECKING:
    from litestar_sandbox.core.settings import DatabaseSettings


def create_sqlalchemy_plugin(database_settings: DatabaseSettings) -> SQLAlchemyPlugin:
    database_config = SQLAlchemyAsyncConfig(
        connection_string=database_settings.database_url,
        before_send_handler="autocommit",
        create_all=True,
    )

    return SQLAlchemyPlugin(database_config)
