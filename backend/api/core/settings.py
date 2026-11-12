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


@dataclass(frozen=True)
class CustodianteSettings:
    """Credencial de um custodiante, por código: `CUSTODIANTE_<CODIGO>_URL` / `_TOKEN`.

    Uma entrada por custodiante no `.env`, nunca uma credencial compartilhada: revogar o acesso
    de um não pode derrubar os outros.
    """

    url_base: str
    token: str

    @classmethod
    def from_env(cls, codigo: str) -> CustodianteSettings:
        prefixo = f"CUSTODIANTE_{codigo.upper()}"
        return cls(url_base=os.environ[f"{prefixo}_URL"], token=os.environ[f"{prefixo}_TOKEN"])


@dataclass(frozen=True)
class SupabaseSettings:
    """Storage do Supabase: API REST própria, não é a conexão do Postgres (DatabaseSettings)."""

    url: str
    service_role_key: str
    bucket: str

    @classmethod
    def from_env(cls) -> SupabaseSettings:
        return cls(
            url=os.environ["SUPABASE_URL"],
            service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
            bucket=os.environ["SUPABASE_STORAGE_BUCKET"],
        )
