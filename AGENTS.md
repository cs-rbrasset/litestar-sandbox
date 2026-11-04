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
- Front-end: só `web-svelte-kit/`, SvelteKit, processo à parte — API pura, sem front same-origin (`CORSConfig` em `app.py`, origem default `http://localhost:5173`). `npm run dev` sobe o Vite; `npm run generate-types` lê o schema direto de `/api/v1/schema/openapi.json`. Já existiram portes em React (`web/`) e Next.js (`web-next/`), descartados depois da comparação.
- Job mais longo (ex.: relatório de posições em várias datas, em PDF) vai pro Prefect como *background task* (`.delay()`), server self-hosted: `prefect server start` + `uv run --env-file .env python -m litestar_sandbox.modules.positions.tasks` sobe o worker (`.serve()`). Sem deployment, sem flow, sem work pool — só a task e o worker que a serve. `--env-file .env` é obrigatório aqui: ao contrário de `litestar run` (que carrega o `.env` sozinho), um `python -m` solto não carrega nada. `PREFECT_API_URL` no `.env` (default `http://127.0.0.1:4200/api`). O Prefect guarda o estado da execução sozinho — sem tabela própria de jobs nem dispatcher. O controller não fala com o Prefect: publica um evento (`core/events.py: publish()`, mesmo mecanismo do `TRADE_SETTLED`) e espera, num `asyncio.Future` embutido no evento, o `task_run_id` que o listener (`positions/listeners.py`) resolve depois de chamar `minha_task.delay(...)` — só o listener importa a task. Consulta de status continua direta (`get_client().read_task_run`), sem evento: é leitura, não efeito colateral. A task roda em processo separado do Litestar: abre a própria sessão com `create_sqlalchemy_config(DatabaseSettings.from_env())`, como os listeners. O PDF vai pro Supabase Storage (`core/storage.py`, credencial `SUPABASE_SERVICE_ROLE_KEY` — não é a do Postgres); o resultado da task é só o path, e quem pede o PDF recebe uma signed URL curta.
- Login via Entra ID: o front é cliente público (MSAL.js, PKCE, sem secret, sem estado no servidor) e fala com o Entra direto — `web-svelte-kit/src/shared/auth/msal.ts` (`msalInstance`, `login()`, `acquireApiToken()`). O backend (`core/entra.py`, `core/auth.py`) nunca participa do login: é só resource server, valida via `Authorization: Bearer` contra o JWKS do tenant (`EntraTokenVerifier`). Credencial enviada é um **access_token** com scope próprio: "Expose an API" foi feito no App registration (scope `access_as_user`), o front pede com `LOGIN_SCOPES = ["api://<client_id>/access_as_user"]`, e o `aud` do access_token continua sendo o client_id puro (não `api://...`). Setup no Entra: **App registration tipo SPA** (pode reusar uma já existente, ex. de outro app com plataforma Web — adicionar plataforma **"Single-page application"** separada, não editar a Web) com redirect URI pra origem do front (`http://localhost:5173`), mais "Expose an API" com o scope `access_as_user` (exige admin consent). `.env` da API: `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` (= o client_id, sem `api://`). `.env.local` do front: `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`. Sem `ENTRA_TENANT_ID` no backend, `build_verifier()` só aceita `AUTH_DEV_TOKENS` — os dois convivem (`CompositeVerifier`). `oid` do Entra vira `u_<oid em minúsculas>` (`DB_ROLE_PATTERN`); o job de espelhamento que cria essa role no Postgres no primeiro login (`db/identity_mirror.sql`, `app.garantir_pessoa`, chamado por `EntraTokenVerifier._ensure_role`) já está implementado.

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

## Checklist: endpoint ou módulo novo no backend

1. Recurso novo e sem relação com `instruments`/`trades`/`positions`? Módulo próprio em `src/litestar_sandbox/modules/<nome>/` (ver `notes/` como referência recente de módulo isolado: `models`, `repositories`, `services`, `protocols`, `controllers`, `deps`, `schemas` — sem `public.py` enquanto nada mais consumir). O `litestar-autowire` descobre `controllers.py`/`listeners.py` sozinho; não precisa registrar nada em `app.py`.
2. Contrato de import-linter novo **no mesmo commit** do módulo (`pyproject.toml`, seção `[tool.importlinter]`). Módulo isolado = dois contratos `forbidden` espelhados (ele não depende de ninguém, ninguém depende dele), igual `notes`. Módulo que consome outro só pelo `public.py` dele = contrato `ignore_imports` no caminho do `public.py`, igual `trades`→`instruments`.
3. Recurso por pessoa (todo mundo só vê o próprio)? Toda rota de dono responde **404, não 403**, pra quem não é dono — nunca revela que o recurso existe pra quem não deveria saber. `request.user.user.db_role` é o identificador estável da pessoa (`core/security.py`); nunca monte uma role a partir de texto do usuário, só o formato de `DB_ROLE_PATTERN`.
4. Sem FK entre módulos. O dado que outro módulo precisa é copiado no registro (ex.: `author_name` copiado da `Identity` no save) ou viaja num evento.
5. Fluxo longo/job assíncrono: controller publica um evento (`core/events.py: publish()`), nunca importa a task/o client do Prefect direto; só o listener do módulo (`listeners.py`) conhece a task. Consulta de status que só lê (sem efeito colateral) pode ir direto, sem evento.
6. Schemas em `msgspec.Struct`; `Parameter(...)` pra restrição em query/path (não `msgspec.Meta`, ignorado fora do body); aliases de DI com `TypeAlias = NamedDependency[SkipValidation[...]]`, nunca `type X = ...`.
7. Teste junto no mesmo commit (`app_client` pra API, sem banco pra lógica de domínio). Pelo menos um teste de isolamento entre duas pessoas quando o recurso for por dono (ver `test_notes_are_isolated_per_owner` como modelo).
8. **Mudou uma tabela que já existe no Postgres compartilhado (Supabase)?** `create_all=True` só cria tabela que falta — nunca altera uma que já existe. Reiniciar a API sozinho não corrige nada; sem um `ALTER TABLE` manual (via `asyncpg`, mesma sessão que você usaria pra inspecionar) a API fica no ar mas quebra em runtime pra quem estiver testando. Isso é temporário: o handoff do banco (ver `README.md`, seção "Autenticação e identidade") prevê migrations com Alembic e a conexão trocando de `postgres` pra `app_login` com privilégio restrito de verdade. Enquanto esse handoff não for aplicado, o passo manual é seu, não pule — mas confira primeiro se já existe `alembic/` ou migration no repo antes de assumir `create_all`.
9. Antes de considerar pronto: `uv run pytest`, `uv run ruff check src tests`, `uv run lint-imports` — os três, sempre, mesmo pra mudança pequena.

## Storybook

- `web-svelte-kit/src/shared/ui/` tem ~45 componentes shadcn-svelte prontos (biblioteca), mas o Storybook (`npm run storybook`) só mostra story de componente **em uso de verdade** em alguma página (`src/pages/`, `src/app/layout/`). Componente novo na biblioteca não ganha `.stories.svelte` ainda.
- Quando um componente passa a ser usado numa página pela primeira vez, o mesmo commit cria a `.stories.svelte` dele (mesmo padrão dos outros: `defineMeta` do `@storybook/addon-svelte-csf`, `<script module lang="ts">`).
- Se um componente para de ser usado em qualquer página, remova a story dele junto.

## Ações destrutivas (front-end)

- Toda exclusão (artigo, boleta, ativo, o que for) passa por `AlertDialog` confirmando antes de executar — nunca `onclick` direto num botão de deletar/cancelar/arquivar. Padrão: `AlertDialogTrigger` no botão, `AlertDialogAction variant="destructive"` disparando a ação de verdade (ver `shared/ui/alert-dialog`, usado em `Trades.svelte`, `Instruments.svelte`, `NotepadEditor.svelte`).

## Checklist: tela nova no front

1. Endpoint novo no backend primeiro, API rodando com ele (reinicie o processo: `litestar run` sem `--reload` não pega controller novo sozinho), **depois** `npm run generate-types` — sem isso os hooks do TanStack Query não têm o que chamar. `openapi-ts.config.ts` lê de `http://localhost:8000/api/v1/schema/openapi.json` por padrão.
2. Estrutura FSD: `src/pages/<feature>/{ui,api,index.ts}`; a rota em `src/app/routes/.../+page.svelte` só importa de `#pages/<feature>/index.ts` e renderiza — nenhuma lógica na rota.
3. `api/<feature>.ts`: `createQuery`/`createMutation` do `@tanstack/svelte-query` recebendo uma função reativa (`() => ({...})`, não um objeto direto — é assim que o resto do app já faz, inclusive pra reler um `id` de prop). Toda chamada do SDK gerado passa por `unwrap()` (`#shared/api/index.ts`). **Toda mutation leva `onError: (error) => notify(describeError(error), true)`** — sem isso, uma falha de verdade fica muda: parece que "não salvou nada" sem motivo nenhum aparente (foi exatamente isso que aconteceu nesta sessão).
4. Componente shadcn só se importa de `#shared/ui/index.ts` (a barrel) — nunca do caminho interno (`#shared/ui/<componente>/<arquivo>.svelte`). O linter de FSD (`npm run lint:fsd`) recusa esse sidestep. Componente que ainda não está na barrel entra lá no mesmo commit que passa a usá-lo.
5. Dois-way binding usa `bind:` (`bind:value`, `bind:checked`, `bind:pressed`) — é o padrão que o resto do app usa em todo lugar (`Select`, `Input`, `Switch`...). Não troque por `value`/`checked` controlado + `onChange`/`onCheckedChange` mesmo que o componente aceite os dois: já causou um bug real aqui (switch não refletia o próprio estado).
6. Prefira ação explícita (botão) a autosave via `$effect` reagindo a toda digitação/toggle — debounce com temporizador dentro de `$effect` é fácil de acertar na superfície e errar na prática; já gerou um loop infinito de requisições nesta sessão. Se o pedido for autosave de verdade, teste contra a API rodando de verdade antes de considerar pronto, não só o typecheck.
7. Depois de qualquer mudança: `npm run typecheck` e `npm run lint:fsd`, os dois, sempre — e teste contra a API real (`curl` nos endpoints, ou o dev server) quando o typecheck sozinho não prova que o fluxo funciona (mutations, navegação, efeitos).
8. Dev server às vezes quebra com `EPERM` em `.svelte-kit/types/...` (corrida de arquivo com outro processo escrevendo, ex. `svelte-check` rodando em paralelo). Limpar `.svelte-kit/` e reiniciar o `npm run dev` resolve.

## Git

- Conventional Commits em português, com o corpo em tópicos explicando o porquê.
- Um assunto por commit.
- Nunca commitar `.env` nem credenciais.
- Working tree com mudanças de outra tarefa, não discutidas com você nesta conversa (código de outro agente, outra sessão, um WIP alheio)? Não commite — nem para "limpar", nem para "aproveitar que já está ali". Sinalize o que achou e separe do que é seu. Se mexer no mesmo arquivo que essa mudança alheia, reconstrua a versão intermediária (stage só a sua parte, commit, restaura o resto em seguida) em vez de misturar os dois num commit só.

## Segurança

- A API exige `Authorization: Bearer` (`core/auth.py`, `_bearer_token`); o verificador é composto (`CompositeVerifier`): tokens fixos de dev sempre, Entra ID (`EntraTokenVerifier`) só com `ENTRA_TENANT_ID` setado. O job de espelhamento que cria a role `u_<oid>` no Postgres pra cada pessoa nova (`db/identity_mirror.sql`, `app.garantir_pessoa`) é chamado no primeiro login de cada pessoa (`EntraTokenVerifier._ensure_role`); sem Postgres (SQLite dos testes) fica desligado.
- Testes de API usam a fixture `app_client`, que já envia o token de teste; para testar a ausência de token, crie um `TestClient` sem o header.
- Código que abre sessão fora de request (listener, job) precisa de `use_identity(...)`: com `DB_ASSUME_IDENTITY=true`, uma transação sem identidade falha no Postgres.
- Nunca construa o nome de uma role a partir de texto do usuário: a `Identity` só aceita o formato de `DB_ROLE_PATTERN`.
