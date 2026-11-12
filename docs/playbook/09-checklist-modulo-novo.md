# 9. Checklist: endpoint ou módulo novo no backend

Use este checklist literalmente, em ordem, pra qualquer recurso novo no backend.

1. **Recurso novo e sem relação com módulos existentes?** Crie módulo próprio em `backend/api/modules/<nome>/`. Comece pelos quatro arquivos obrigatórios — `models.py`, `services.py`, `controllers.py`, `schemas.py` — e **crie o resto só quando precisar** (capítulo 3). O autowire descobre `controllers.py`/`listeners.py` sozinho e `core.jobs.servir()` descobre `tasks.py` — não precisa registrar nada em `app.py` nem no `worker.py`. O model SQLAlchemy de verdade entra em `database/models/<área>/model.py`; o `models.py` do módulo é só o shim.

2. **Contrato de import-linter novo, no mesmo commit do módulo** (`backend/api/pyproject.toml`, seção `[tool.importlinter]`):
   - Módulo isolado = dois contratos `forbidden` espelhados (ele não depende de ninguém, ninguém depende dele).
   - Módulo que consome outro só pelo `public.py` dele = contrato `ignore_imports` liberando esse caminho específico.
   - Área nova em `database.models` = um contrato `forbidden` dizendo que só o módulo dono a importa.
   - Tem `domain/` ou parsers? Contrato de pureza (sem banco, framework, rede).

3. **Recurso por pessoa (todo mundo só vê o próprio)?** Toda rota de dono responde **404, não 403** pra quem não é dono. O identificador estável de pessoa vem sempre do mecanismo de auth (capítulo 5), nunca montado a partir de texto vindo do usuário.

4. **Sem FK entre módulos** — nem entre áreas do `database`. O dado que outro módulo precisa é copiado no registro (ex.: nome copiado de outra tabela no momento do save) ou viaja num evento. O teste de FK por área, no próprio pacote `database`, fiscaliza isso.

5. **Fluxo longo / job assíncrono:** controller → service → `core.jobs.enfileirar` (capítulo 4). Nenhum arquivo de `modules/` importa o orquestrador. Consulta de status vai direto em `core.jobs.status` — é leitura pura. **Evento (`core/events.py`) é pra avisar outro módulo, não pra disparar job.**

6. **Schemas em `msgspec.Struct`**; restrição de query/path em `QueryParameter(...)`/`Parameter(...)` dentro de `Annotated[...]` (não `msgspec.Meta`, que é ignorado fora do body, e não como valor default, que o linter recusa); aliases de DI com `TypeAlias = NamedDependency[SkipValidation[...]]`, nunca `type X = ...`.

7. **Teste junto no mesmo commit**: `app_client` pra API, sem banco pra lógica de domínio, fixture de arquivo real pra parser. Pelo menos um teste de isolamento entre duas pessoas quando o recurso for por dono.

8. **Mudou uma tabela que já existe no banco compartilhado de produção/homolog?** Ver capítulo 11 — `create_all` só cria tabela faltante, nunca altera uma existente.

9. **Antes de considerar pronto**, dentro de `backend/api/`: `uv run pytest`, `uv run ruff check .`, `uv run lint-imports` — os três, sempre, mesmo pra mudança pequena. Mexeu no pacote `database`? `uv run pytest` lá também.
