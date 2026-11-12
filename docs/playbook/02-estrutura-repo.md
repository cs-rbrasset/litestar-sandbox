# 2. Estrutura do repositório

## Layout de pastas

```
root/
├── docs/                   # documentação geral (este playbook, decisões de arquitetura)
├── frontend/               # SvelteKit, processo à parte, FSD
├── backend/
│   ├── api/                # a API em si — core/ + modules/, flat, sem pacote wrapper
│   │                       #   app.py (web) e worker.py (jobs) são as duas metades

│   ├── mcp/                # servidor MCP, se o projeto expuser ferramentas pra agentes [AJUSTAR: pode não existir]
│   └── external/           # projetos externos vendorizados, cada pasta um projeto separado [AJUSTAR]
└── database/               # models SQLAlchemy compartilhados, pacote próprio no workspace
```

`backend/mcp/` e `backend/external/` existem como lugar reservado mesmo quando vazios — deixa claro, pra quem entra no repo (humano ou agente), que "serve MCP" e "vendorizar projeto externo" têm endereço certo, em vez de alguém inventar um na hora.

## Workspace `uv`

A raiz do repo **não tem `[project]` próprio** — só `[tool.uv.workspace]` apontando pros membros (`backend/api`, `database`). Cada membro tem seu próprio `pyproject.toml` com suas próprias dependências e seus próprios gates (ruff, import-linter, pytest config).

```toml
# pyproject.toml da raiz
[tool.uv.workspace]
members = ["backend/api", "database"]
```

`uv sync` na raiz resolve os dois membros de uma vez, com um lockfile único (`uv.lock` na raiz) — isso garante que a API e o pacote `database` nunca ficam com versões divergentes de uma dependência compartilhada (ex.: SQLAlchemy).

Comandos de backend (pytest, ruff, lint-imports, rodar a API) executam de dentro de `backend/api/`, não da raiz — porque é lá que o `pyproject.toml` com esses gates mora. Os contratos de import ficam todos nesse `pyproject.toml`, com `database` entre os `root_packages`: um `lint-imports` só cobre os três pacotes.

## `database/` como pacote separado

`database/` não é uma pasta de "utils" dentro da API — é um pacote Python de primeira classe no workspace, publicado num PyPI privado e consumido por outros softwares da RBR (ver capítulo 3: ele é **contrato público**, com versionamento semântico e migrations versionadas junto).

Isso força uma regra de dependência num sentido só: `database` nunca importa nada de `backend/api`. Se `database` precisasse importar algo da API, a separação em pacote não faria sentido. Ele tem testes próprios (`uv run pytest` de dentro de `database/`), entre eles o que garante que nenhuma FK cruza área.

## Front-end como processo à parte

`frontend/` não fica same-origin com a API. É um SvelteKit rodando com seu próprio dev server (Vite), falando com a API via HTTP com CORS configurado explicitamente (origem de dev, tipicamente `http://localhost:5173`). Isso significa:

- A API nunca serve HTML/assets do front.
- Deploy do front e do back são independentes (podem até escalar separado).
- O client TypeScript do front é **gerado a partir do schema OpenAPI da API** (`npm run generate-types` lendo `/api/v1/schema/openapi.json`), não escrito à mão — isso elimina uma classe inteira de bug de "front e back dessincronizaram o contrato".

## `docs/` geral

Guarda decisões de arquitetura que não são nem código nem este playbook de processo — ex.: por que se escolheu SvelteKit em vez de React/Next (ver histórico de decisão no próprio repo), ou outras decisões de stack que merecem registro além do commit message.
