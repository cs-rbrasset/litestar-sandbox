# Guia para agentes de IA

Nesta branch os agentes estão liberados para implementar: funções completas, módulos novos, refatorações e testes. O modo tutor (explicar e revisar, sem escrever a implementação) continua valendo na `feat/api-inicial` e na `main`.

## Comandos

- Dependências com `uv`.
- Antes de qualquer commit, os três precisam passar:
  - `uv run pytest`
  - `uv run ruff check src tests`
  - `uv run lint-imports`
- Subir a API: `uv run litestar --app litestar_sandbox.app:create_app run`. O banco vem de `DATABASE_URL` no `.env`, que não vai para o repositório.
- Os testes usam SQLite, um arquivo por teste em `tmp_path` (fixtures em `tests/conftest.py`).
- Front-end em `web/` (React + Vite, servido pela API com o litestar-vite): `VITE_DEV_MODE=true uv run litestar ... run` sobe API e Vite juntos. Mudou a API? `uv run litestar --app litestar_sandbox.app:create_app assets generate-types` e depois `cd web && npx tsc -b --noEmit`. No Windows, use `PYTHONUTF8=1` na CLI do litestar-vite.
- Não registre o prefixo `/api/v1` em `Litestar(path=...)`: ele fica no `ApiRouter` (ver `app.py`), senão a SPA sai de `/`.

## Arquitetura

- Monólito modular: `core` e os módulos `instruments`, `trades` e `positions`, em `src/litestar_sandbox/modules/`.
- Um módulo só importa outro pelo `public.py` dele. As regras estão nos contratos do import-linter, no `pyproject.toml`. Módulo novo ganha contratos novos no mesmo commit.
- `core` não importa nenhum módulo.
- Sem FK entre tabelas de módulos diferentes. O dado que outro módulo precisa é copiado no registro ou viaja no evento.
- O `litestar-autowire` monta o app: descobre os `Controller` de `controllers.py` e os `EventListener` de `listeners.py` em cada módulo. O `app.py` não importa módulos. Cada controller declara o próprio `path` (`/instruments`, `/trades`...).
- Listener é definido no nível do módulo e recebe `app` do `publish`; a config do banco vem de `get_sqlalchemy_config(app)`.
- Arquivos por módulo: `models`, `repositories`, `services`, `controllers`, `deps`, `protocols`, `schemas`, `public`. Crie `domain.py` só quando houver regra de negócio que valha testar sem banco.

## Convenções

- Schemas com `msgspec.Struct`. A validação de formato fica na borda HTTP.
- Em query e path params, restrições vão em `Parameter(...)`: o `msgspec.Meta` é ignorado fora do body.
- Aliases de DI: `X: TypeAlias = NamedDependency[SkipValidation[...]]`. Não use `type X = ...` (PEP 695): quebra o `SkipValidation` no DI do Litestar. O `UP040` fica ignorado com `# noqa: UP040`.
- Services herdam de `SQLAlchemyAsyncRepositoryService`. Para `with_for_update`, use `self.repository.get(...)`: o `get` do service não aceita o parâmetro.
- Código que roda fora do request (listeners, workers) abre a própria sessão com `config.get_session()`, usa a mesma config do plugin, faz commit à mão e é idempotente.
- Datas de negócio são `datetime.date`, não `datetime.datetime`.

## Testes

- Comportamento novo vem com teste. Testes de API usam a fixture `app_client`.
- Lógica de domínio é testada sem banco.
- Teste que depende de Postgres (por exemplo, `FOR UPDATE`) é pulado quando o banco for SQLite.

## Git

- Conventional Commits em português, com o corpo em tópicos explicando o porquê.
- Um assunto por commit.
- Nunca commitar `.env` nem credenciais.

## Segurança

- A API exige `Authorization: Bearer` (`core/auth.py`), mas o único verificador é o de tokens fixos de dev. Não exponha endpoints de escrita por MCP antes do verificador do Entra ID.
- Testes de API usam a fixture `app_client`, que já envia o token de teste; para testar a ausência de token, crie um `TestClient` sem o header.
- Código que abre sessão fora de request (listener, job) precisa de `use_identity(...)`: com `DB_ASSUME_IDENTITY=true`, uma transação sem identidade falha no Postgres.
- Nunca construa o nome de uma role a partir de texto do usuário: a `Identity` só aceita o formato de `DB_ROLE_PATTERN`.
