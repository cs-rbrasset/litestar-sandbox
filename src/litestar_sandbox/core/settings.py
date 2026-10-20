import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    database_url: str

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        return cls(database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sandbox.db"))
