import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    database_url: str
    # SET LOCAL ROLE por transação (core/database.py). Ligue só depois de aplicar
    # db/identity.sql: sem a função app.assumir_identidade, toda transação falha.
    assume_identity: bool = False

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sandbox.db"),
            assume_identity=os.getenv("DB_ASSUME_IDENTITY", "false").lower()
            in {"1", "true", "yes"},
        )
