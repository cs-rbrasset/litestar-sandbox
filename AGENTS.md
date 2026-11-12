# Guia para agentes de IA

Nesta branch os agentes estão liberados para implementar: funções completas, módulos novos, refatorações e testes. O modo tutor (explicar e revisar, sem escrever a implementação) continua valendo na `feat/api-inicial` e na `main`.

## Estrutura do repositório

Workspace do `uv` com dois membros Python (`backend/api`, `database`) — a raiz só tem `[tool.uv.workspace]`, sem `[project]` próprio.

```
root/
├── docs/              # documentação geral do projeto (decisões de arquitetura etc.)
├── frontend/          # SvelteKit, processo à parte (era web-svelte-kit/)
├── backend/
│   ├── api/           # a API — core/ + modules/, flat, sem pacote wrapper
│   ├── mcp/           # servidor MCP (vazio por enquanto)
│   └── external/      # projetos externos, cada pasta um projeto separado (vazio por enquanto)
└── database/          # models SQLAlchemy compartilhados, pensado pra virar pacote instalável à parte
```

## Comandos

- Dependências com `uv` (workspace na raiz — `uv sync` resolve os dois membros de uma vez).
- Os comandos de backend abaixo rodam com `cd backend/api` primeiro (cada membro do workspace tem seu próprio `pyproject.toml`/gates).
- Antes de qualquer commit, os três precisam passar (dentro de `backend/api/`):
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run lint-imports`
- Subir a API: `cd backend/api && uv run litestar --app app:create_app run`. O banco vem de `DATABASE_URL` no `.env` **da raiz do repositório** (python-dotenv sobe os diretórios até achar; não precisa de `.env` dentro de `backend/api/`), que não vai para o repositório.
- Os testes usam SQLite, um arquivo por teste em `tmp_path` (fixtures em `backend/api/tests/conftest.py`).
- Front-end: só `frontend/`, SvelteKit, processo à parte — API pura, sem front same-origin (`CORSConfig` em `app.py`, origem default `http://localhost:5173`). `npm run dev` sobe o Vite; `npm run generate-types` lê o schema direto de `/api/v1/schema/openapi.json`. Já existiram portes em React e Next.js, descartados depois da comparação.
- Job longo (relatório em PDF, importação de custodiante) passa pela porta `core/jobs.py` — **o único arquivo do backend que importa `prefect`** (contrato do import-linter fiscaliza). Módulo declara com `@job(nome, tentativas=, intervalo_s=, nao_repetir=(ExcecaoDeDominio,))` em `tasks.py`, dispara com `await enfileirar(job, **params)` (devolve o id na hora) e consulta com `await status(id)`. Sessão de banco dentro do job: `async with sessao_de_job()` — uma engine por execução, com `dispose()` garantido. Fluxo HTTP: **controller → service → `enfileirar`**; não existe mais evento + `asyncio.Future` pra disparar job. Server: `prefect server start`; worker: `cd backend/api && uv run --env-file ../../.env python worker.py` (`worker.py` fica ao lado do `app.py` e descobre `modules/*/tasks.py` sozinho). `--env-file` é obrigatório: ao contrário de `litestar run`, um `python` solto não carrega o `.env`. `PREFECT_API_URL` no `.env` (default `http://127.0.0.1:4200/api`). O Prefect guarda o estado da execução — sem tabela de jobs nem dispatcher. **O worker não tem app Litestar: job não publica evento** — pra falar com outro módulo, chama o `public.py` dele. Arquivo gerado vai pro object storage (`core/storage.py`, porta `put`/`get`/`list`/`url_assinada`, credencial `SUPABASE_SERVICE_ROLE_KEY` — não é a do Postgres); o resultado do job é só o path, e quem pede o arquivo recebe uma signed URL curta.
- Evento (`core/events.py: publish()`) é só pra **um módulo avisar outro dentro do app** (ex.: `TRADE_SETTLED` de `boletas` → `posicoes/listeners.py`). Não é mecanismo de disparo de job.
- Login via Entra ID: o front é cliente público (MSAL.js, PKCE, sem secret, sem estado no servidor) e fala com o Entra direto — `frontend/src/shared/auth/msal.ts` (`msalInstance`, `login()`, `acquireApiToken()`). O backend (`core/entra.py`, `core/auth.py`) nunca participa do login: é só resource server, valida via `Authorization: Bearer` contra o JWKS do tenant (`EntraTokenVerifier`). Credencial enviada é um **access_token** com scope próprio: "Expose an API" foi feito no App registration (scope `access_as_user`), o front pede com `LOGIN_SCOPES = ["api://<client_id>/access_as_user"]`, e o `aud` do access_token continua sendo o client_id puro (não `api://...`). Setup no Entra: **App registration tipo SPA** (pode reusar uma já existente, ex. de outro app com plataforma Web — adicionar plataforma **"Single-page application"** separada, não editar a Web) com redirect URI pra origem do front (`http://localhost:5173`), mais "Expose an API" com o scope `access_as_user` (exige admin consent). `.env` da API: `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` (= o client_id, sem `api://`). `.env.local` do front: `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`. Sem `ENTRA_TENANT_ID` no backend, `build_verifier()` só aceita `AUTH_DEV_TOKENS` — os dois convivem (`CompositeVerifier`). `oid` do Entra vira `u_<oid em minúsculas>` (`DB_ROLE_PATTERN`); o job de espelhamento que cria essa role no Postgres no primeiro login (`database/ddl/identity_mirror.sql`, `app.garantir_pessoa`, chamado por `EntraTokenVerifier._ensure_role`) já está implementado.

## Arquitetura

- Monólito modular: `core` e os módulos `ativos`, `boletas`, `posicoes`, `notas`, `custodiante`, `carteira` e `extrato`, em `backend/api/modules/` — flat, sem pacote wrapper (`from core.X import Y`, `from modules.boletas.X import Y`, direto).
- Integração externa (`custodiante` → `carteira.public`/`extrato.public`): gateway só faz I/O e devolve `list[ArquivoBruto]`; parser é função pura `Sequence[ArquivoBruto] -> canônico`. O job faz **baixar → guardar bruto → parsear → registrar**, nessa ordem, sem fundir etapas; reprocessar é **ler bruto → parsear → registrar**. Custodiante novo = gateway + parser + fixture + uma linha em `registro.py`. Detalhe no capítulo 14 do playbook (`docs/playbook/14-integracoes-externas.md`).
- Critério pra entrar no `core`: infraestrutura sem regra de negócio **e** usada por pelo menos dois módulos. `core` nunca cita módulo pelo nome — quando precisa varrer, recebe o nome do pacote como string.
- Um módulo só importa outro pelo `public.py` dele. As regras estão nos contratos do import-linter, no `backend/api/pyproject.toml` (`root_packages = ["core", "modules", "database"]`, mais `include_external_packages` e `exclude_type_checking_imports`). Módulo novo ganha contratos novos no mesmo commit — incluindo o da área nova em `database.models` e o de pureza, se tiver `domain/` ou `parsers/`.
- `core` não importa nenhum módulo.
- **Models SQLAlchemy moram em `database/`, não dentro do módulo.** `database/models/<área>/model.py` (hoje: `ativos`, `boletas`, `posicoes`, `notas`, `carteira`, `extrato` — `custodiante` não tem área, porque o bruto mora no object storage) declara a classe ORM de verdade — e os enums que as colunas usam, se tiver (`database/models/<área>/enums.py`). O `models.py`/`enums.py` dentro de `backend/api/modules/<área>/` é só um shim de re-export (`from database.models.<área>.model import X`) — o resto do módulo (`services.py`, `controllers.py`, `repositories.py`...) continua importando do `models.py` local, sem saber que é um re-export. `database` é pacote próprio no workspace do `uv` (pensado pra virar instalável à parte no futuro) e **nunca importa nada de `backend/api`** — a dependência é só num sentido.
- Sem FK entre tabelas de módulos diferentes. O dado que outro módulo precisa é copiado no registro ou viaja no evento.
- O `litestar-autowire` monta o app: descobre os `Controller` de `controllers.py` e os `EventListener` de `listeners.py` em cada módulo. O `app.py` não importa módulos. Cada controller declara o próprio `path` (`/ativos`, `/boletas`...).
- Listener é definido no nível do módulo e recebe `app` do `publish`; a config do banco vem de `get_sqlalchemy_config(app)`.
- Arquivos por módulo: **obrigatórios** são `models.py` (shim pro `database/`), `services.py`, `controllers.py` e `schemas.py`. Todo o resto nasce sob demanda — `repositories.py`, `deps.py`, `protocols.py`, `enums.py`, `domain/`, `public.py`, `tasks.py`, `listeners.py`. Não crie arquivo vazio "pra seguir o padrão".
- Modelo canônico (`domain/`) ≠ ORM (`database/`) ≠ contrato HTTP (`schemas.py`). `domain/` e `parsers/` são **puros**: sem sqlalchemy, advanced_alchemy, prefect, litestar, httpx, niquests, playwright nem `database` (contrato do import-linter). Vocabulário fechado usado nos dois lados é copiado de propósito — `StrEnum` no `domain/` é a fonte de verdade, `database` guarda a lista de strings pro `CHECK`, e um teste compara as duas.
- O pacote `database` é **contrato público** (publicável num PyPI privado, consumido por outros softwares da RBR): versionamento semântico (remover/renomear coluna = versão maior), migrations versionadas junto, FK só dentro da mesma área (teste no próprio pacote varre o `MetaData`), e `database` não importa `core` nem `modules`.

## Convenções

- Schemas com `msgspec.Struct`. A validação de formato fica na borda HTTP.
- Em query e path params, restrições vão em `Parameter(...)`: o `msgspec.Meta` é ignorado fora do body.
- Aliases de DI: `X: TypeAlias = NamedDependency[SkipValidation[...]]`. Não use `type X = ...` (PEP 695): quebra o `SkipValidation` no DI do Litestar. O `UP040` fica ignorado com `# noqa: UP040`.
- Services herdam de `SQLAlchemyAsyncRepositoryService`. Para `with_for_update`, use `self.repository.get(...)`: o `get` do service não aceita o parâmetro.
- Código que roda fora do request faz commit à mão e é idempotente. **Listener** (tem `app`) usa `get_sqlalchemy_config(app).get_session()`; **job** (não tem `app`) usa `sessao_de_job()` do `core/jobs.py`, que já declara a identidade de sistema e cuida da engine.
- Escrita que o job faz é **upsert por chave de negócio** (`INSERT ... ON CONFLICT`), nunca "busca e depois insere" — e só sobrescreve quando a coleta é mais nova que a gravada, exceto em reprocessamento forçado explicitamente.
- Datas de negócio são `datetime.date`, não `datetime.datetime`.

## Testes

- Comportamento novo vem com teste. Testes de API usam a fixture `app_client`.
- Lógica de domínio é testada sem banco.
- Teste que depende de Postgres (por exemplo, `FOR UPDATE`) é pulado quando o banco for SQLite.

## Checklist: endpoint ou módulo novo no backend

1. Recurso novo e sem relação com os módulos existentes? Módulo próprio em `backend/api/modules/<nome>/`, começando pelos quatro arquivos obrigatórios (ver `notas/` como módulo isolado simples, `custodiante/` como módulo de integração). O `litestar-autowire` descobre `controllers.py`/`listeners.py` e o `core.jobs.servir()` descobre `tasks.py`; não precisa registrar nada em `app.py` nem no `worker.py`. O model SQLAlchemy de verdade entra em `database/models/<área>/model.py` (ver seção Arquitetura) — o `models.py` do módulo é só o shim.
2. Contrato de import-linter novo **no mesmo commit** do módulo (`backend/api/pyproject.toml`, seção `[tool.importlinter]`). Módulo isolado = dois contratos `forbidden` espelhados (ele não depende de ninguém, ninguém depende dele), igual `notas`. Módulo que consome outro só pelo `public.py` dele = contrato `ignore_imports` no caminho do `public.py`, igual `boletas`→`ativos` e `custodiante`→`carteira`/`extrato`. Área nova no `database` = contrato dizendo que só o módulo dono a importa. `domain/` ou `parsers/` = contrato de pureza.
3. Recurso por pessoa (todo mundo só vê o próprio)? Toda rota de dono responde **404, não 403**, pra quem não é dono — nunca revela que o recurso existe pra quem não deveria saber. `request.user.user.db_role` é o identificador estável da pessoa (`core/security.py`); nunca monte uma role a partir de texto do usuário, só o formato de `DB_ROLE_PATTERN`.
4. Sem FK entre módulos. O dado que outro módulo precisa é copiado no registro (ex.: `author_name` copiado da `Identity` no save) ou viaja num evento.
5. Fluxo longo/job assíncrono: **controller → service → `core.jobs.enfileirar`**. Nenhum arquivo de `modules/` importa `prefect`. Consulta de status vai direto em `core.jobs.status` (leitura pura). Evento é pra avisar outro módulo, não pra disparar job.
6. Schemas em `msgspec.Struct`; restrição de query/path em `QueryParameter(...)`/`Parameter(...)` **dentro de `Annotated[...]`** (não `msgspec.Meta`, ignorado fora do body; não como valor default, que o ruff recusa com `B008`); aliases de DI com `TypeAlias = NamedDependency[SkipValidation[...]]`, nunca `type X = ...`.
7. Teste junto no mesmo commit (`app_client` pra API, sem banco pra lógica de domínio). Pelo menos um teste de isolamento entre duas pessoas quando o recurso for por dono (ver `test_notes_are_isolated_per_owner` como modelo).
8. **Mudou uma tabela que já existe no Postgres compartilhado (Supabase)?** `create_all=True` só cria tabela que falta — nunca altera uma que já existe. Reiniciar a API sozinho não corrige nada; sem um `ALTER TABLE` manual (via `asyncpg`, mesma sessão que você usaria pra inspecionar) a API fica no ar mas quebra em runtime pra quem estiver testando. Isso é temporário: o handoff do banco (ver `README.md`, seção "Autenticação e identidade") prevê migrations com Alembic e a conexão trocando de `postgres` pra `app_login` com privilégio restrito de verdade. Enquanto esse handoff não for aplicado, o passo manual é seu, não pule — mas confira primeiro se já existe `alembic/` ou migration no repo antes de assumir `create_all`.
9. Antes de considerar pronto, dentro de `backend/api/`: `uv run pytest`, `uv run ruff check .`, `uv run lint-imports` — os três, sempre, mesmo pra mudança pequena. Mexeu no pacote `database`? `uv run pytest` dentro de `database/` também.

## Storybook

- `frontend/src/shared/ui/` tem ~45 componentes shadcn-svelte prontos (biblioteca), mas o Storybook (`npm run storybook`) só mostra story de componente **em uso de verdade** em alguma página (`src/pages/`, `src/app/layout/`). Componente novo na biblioteca não ganha `.stories.svelte` ainda.
- Quando um componente passa a ser usado numa página pela primeira vez, o mesmo commit cria a `.stories.svelte` dele (mesmo padrão dos outros: `defineMeta` do `@storybook/addon-svelte-csf`, `<script module lang="ts">`).
- Se um componente para de ser usado em qualquer página, remova a story dele junto.
- **`npm run storybook` trava nesta máquina (Windows).** Reproduzido de forma consistente em `storybook@10.6.5` e `10.6.7`, com e sem `@storybook/addon-a11y`: o processo Node fica preso em loop (~1 núcleo a 100%, minutos a fio) servindo `/sb-preview/runtime.js` (confirmado via `curl` direto, sem navegador — não é bug de story nem de addon isolado). `@storybook/addon-a11y` está desligado em `.storybook/main.ts` por precaução, mas o travamento acontece mesmo assim. Não investigado além disso (sem WSL disponível nesta máquina); se for crítico, testar em outra máquina/Linux ou abrir issue upstream em `@storybook/sveltekit`.

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

- A API exige `Authorization: Bearer` (`core/auth.py`, `_bearer_token`); o verificador é composto (`CompositeVerifier`): tokens fixos de dev sempre, Entra ID (`EntraTokenVerifier`) só com `ENTRA_TENANT_ID` setado. O job de espelhamento que cria a role `u_<oid>` no Postgres pra cada pessoa nova (`database/ddl/identity_mirror.sql`, `app.garantir_pessoa`) é chamado no primeiro login de cada pessoa (`EntraTokenVerifier._ensure_role`); sem Postgres (SQLite dos testes) fica desligado.
- Testes de API usam a fixture `app_client`, que já envia o token de teste; para testar a ausência de token, crie um `TestClient` sem o header.
- Código que abre sessão fora de request (listener, job) precisa de `use_identity(...)`: com `DB_ASSUME_IDENTITY=true`, uma transação sem identidade falha no Postgres.
- Nunca construa o nome de uma role a partir de texto do usuário: a `Identity` só aceita o formato de `DB_ROLE_PATTERN`.
