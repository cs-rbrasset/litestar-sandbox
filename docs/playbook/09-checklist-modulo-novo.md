# 9. Checklist: endpoint ou módulo novo no backend

Use este checklist literalmente, em ordem, pra qualquer recurso novo no backend.

1. **Recurso novo e sem relação com módulos existentes?** Crie módulo próprio em `backend/api/modules/<nome>/`. Use um módulo isolado recente como referência de forma (`models`, `repositories`, `services`, `protocols`, `controllers`, `deps`, `schemas` — sem `public.py` enquanto nada mais consumir). O autowire descobre `controllers.py`/`listeners.py` sozinho — não precisa registrar nada em `app.py`. O model SQLAlchemy de verdade entra em `database/models/<nome>/model.py` (capítulo 3) — o `models.py` do módulo é só o shim.

2. **Contrato de import-linter novo, no mesmo commit do módulo** (`backend/api/pyproject.toml`, seção `[tool.importlinter]`):
   - Módulo isolado = dois contratos `forbidden` espelhados (ele não depende de ninguém, ninguém depende dele).
   - Módulo que consome outro só pelo `public.py` dele = contrato `ignore_imports` liberando esse caminho específico.

3. **Recurso por pessoa (todo mundo só vê o próprio)?** Toda rota de dono responde **404, não 403** pra quem não é dono. O identificador estável de pessoa vem sempre do mecanismo de auth (capítulo 5), nunca montado a partir de texto vindo do usuário.

4. **Sem FK entre módulos.** O dado que outro módulo precisa é copiado no registro (ex.: nome copiado de outra tabela no momento do save) ou viaja num evento.

5. **Fluxo longo / job assíncrono:** controller publica um evento (capítulo 4), nunca importa a task/o client do orquestrador direto; só o listener do módulo conhece a task. Consulta de status que só lê (sem efeito colateral) pode ir direto, sem evento.

6. **Schemas em `msgspec.Struct`**; `Parameter(...)` pra restrição em query/path (não `msgspec.Meta`, que é ignorado fora do body); aliases de DI com `TypeAlias = NamedDependency[SkipValidation[...]]`, nunca `type X = ...`.

7. **Teste junto no mesmo commit** (`app_client` pra API, sem banco pra lógica de domínio). Pelo menos um teste de isolamento entre duas pessoas quando o recurso for por dono.

8. **Mudou uma tabela que já existe no banco compartilhado de produção/homolog?** Ver capítulo 11 — `create_all` só cria tabela faltante, nunca altera uma existente.

9. **Antes de considerar pronto**, dentro de `backend/api/`: `uv run pytest`, `uv run ruff check .`, `uv run lint-imports` — os três, sempre, mesmo pra mudança pequena.
