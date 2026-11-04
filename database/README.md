# database

Models SQLAlchemy compartilhados, organizados por área de negócio (`models/<área>/`). Não
importa nada de `backend/api` — a dependência é sempre no sentido `backend/api` → `database`,
nunca o contrário, pra esse pacote poder ser publicado/instalado à parte no futuro.

- `models/` — um subpacote por área (hoje: `instruments`, `trades`, `positions`, `notes`),
  cada um com o(s) model(s) SQLAlchemy e os enums que as colunas usam.
- `ddl/` — SQL de setup que não é gerado pelo `create_all` da aplicação (roles, funções,
  triggers de identidade — ver `ddl/identity.sql`).
- `docs/` — documentação do banco (dbdocs ou equivalente).
