import os

from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig, SQLAlchemyPlugin

database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sandbox.db")

database_config = SQLAlchemyAsyncConfig(
    connection_string=database_url,
    before_send_handler="autocommit",
    create_all=True
)

sqlalchemy_plugin = SQLAlchemyPlugin(database_config)
