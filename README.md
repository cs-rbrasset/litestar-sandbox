# litestar-sandbox

Sandbox para aprender [Litestar](https://docs.litestar.dev/) construindo um **monólito modular** com [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/). O domínio é o de uma **gestora de recursos** (cadastro de ativos, operações, posições), e o projeto serve de modelo para uma API real de uma gestora de porte médio.

Por enquanto o banco é SQLite, inclusive na POC. O projeto real vai usar PostgreSQL.

## Como rodar

Requisito: [uv](https://docs.astral.sh/uv/). Ele instala o Python 3.14 e as dependências sozinho.

```bash
uv sync
uv run litestar --app litestar_sandbox.app:create_app run --reload
```

- API: <http://127.0.0.1:8000/api/v1>
- Swagger: <http://127.0.0.1:8000/api/v1/schema/swagger>

O `app.py` expõe uma fábrica (`create_app`), e não uma instância pronta. Por isso o `--app` aponta para a função.

O banco é um arquivo `sandbox.db` criado no diretório onde você roda o comando, com as tabelas geradas no startup. Para usar outro banco, defina a variável `DATABASE_URL`:

```bash
DATABASE_URL="sqlite+aiosqlite:///./outro.db" uv run litestar --app litestar_sandbox.app:create_app run
```

O `create_all` só cria tabelas que ainda não existem: ele não acrescenta colunas novas a uma tabela existente. Depois de mudar um model, apague o `sandbox.db`. (Migrations com Alembic estão no roadmap.)

### Endpoints

Todas as rotas ficam sob o prefixo `/api/v1`.

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/ping` | health check |
| GET | `/instruments` | lista os ativos ativos, com paginação (`currentPage`, `pageSize`), busca por nome ou código CETIP (`searchString`) e ordenação (`orderBy`, `sortOrder`) |
| POST | `/instruments` | cria um ativo (form-urlencoded). O código CETIP é normalizado para maiúsculas, sem espaços nas pontas, e nunca é reaproveitado (`409` se repetido) |
| GET | `/instruments/{id}` | busca um ativo por id (`404` se não existir ou estiver desativado) |
| PATCH | `/instruments/{id}` | atualização parcial (JSON). Só o `name` é editável; campos ausentes não mudam |
| DELETE | `/instruments/{id}` | desativa o ativo (soft delete) e responde `204` |

Campos de um ativo:

| Campo | Regra |
| --- | --- |
| `cetip_code` | identificador do ativo no mercado. Letras e números, de 4 a 20 caracteres; único e imutável |
| `name` | de 1 a 200 caracteres |
| `instrument_type` | `CRI`, `DEB`, `CDB` ou `LCI`. Validado na API e por um `CHECK` no banco; imutável |

O preço não faz parte do cadastro: em renda fixa ele é o PU de cada data, uma série temporal que pertence a um módulo próprio.

### Boletas (`/trades`)

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/trades` | registra uma boleta (JSON). O ativo é validado pelo `instruments.public`: se não existir ou estiver desativado, `400`. O código CETIP é copiado do ativo no momento do registro, e o status começa em `PENDING` |
| GET | `/trades` | lista as boletas, com paginação, busca por `fund_cnpj` ou `cetip_code` e ordenação (padrão: `trade_date` decrescente) |
| GET | `/trades/{id}` | busca uma boleta por id |
| POST | `/trades/{id}/settle` | liquida a boleta (`PENDING → SETTLED`). Responde `200`, ou `409` se ela não estiver pendente |
| POST | `/trades/{id}/cancel` | cancela a boleta (`PENDING → CANCELLED`). Responde `200`, ou `409` se ela não estiver pendente |

Boletas não são editadas nem apagadas: uma boleta errada é cancelada e registrada de novo.

| Campo | Regra |
| --- | --- |
| `fund_cnpj` | 14 dígitos, sem pontuação |
| `instrument_id` | id de um ativo ativo; referência sem chave estrangeira, porque a tabela é de outro módulo |
| `trade_date` | data no formato ISO (`2026-10-16`) |
| `side` | `BUY` ou `SELL` |
| `quantity` | inteiro maior que zero (CRI, DEB, CDB e LCI são negociados em unidades) |
| `unit_price` | PU, decimal maior que zero, com até 8 casas |

### Qualidade

```bash
uv run ruff check src tests     # lint
uv run ruff format src tests    # formatação
uv run ty check                 # checagem de tipos
uv run lint-imports             # fronteiras entre módulos
uv run pytest                   # testes (cada teste usa um banco SQLite temporário)
```

## Arquitetura

```text
src/litestar_sandbox/
├── app.py                  # create_app(): registra os módulos sob /api/v1
├── core/                   # compartilhado; não conhece nenhum módulo
│   ├── settings.py         # DatabaseSettings (lê DATABASE_URL)
│   ├── database.py         # config do SQLAlchemy e plugin
│   └── deps.py             # aliases de injeção de dependência genéricos (FilterDep, SessionDep)
└── modules/
    ├── instruments/        # cadastro de ativos
    │   ├── __init__.py     # instruments_router
    │   ├── public.py       # a ÚNICA porta para outros módulos
    │   ├── controllers.py  # HTTP
    │   ├── deps.py         # alias de DI do service e config dos filtros
    │   ├── protocols.py    # contrato do service usado pelo controller
    │   ├── enums.py        # InstrumentType (re-exportado pelo public.py)
    │   ├── schemas.py      # DTOs de entrada HTTP (msgspec)
    │   ├── services.py     # regras de negócio
    │   ├── repositories.py # acesso a dados
    │   └── models.py       # tabelas
    └── trades/             # boletas; usa o instruments só pelo public.py
```

Uma requisição percorre as camadas nesta ordem: controller → service → repository → model.

### Regras entre módulos

- **Cada módulo é dono dos seus dados.** Nenhum módulo lê as tabelas de outro, e não há chave estrangeira entre tabelas de módulos diferentes.
- **Outro módulo só acessa um módulo pelo `public.py` dele**, que expõe um Protocol (o contrato), DTOs imutáveis e um provider para a injeção de dependência. Objetos ORM nunca saem do módulo.
- **O `core/` não importa nada de `modules/`**, e as dependências entre módulos vão num sentido só.
- **As regras são verificadas por ferramenta**: o [import-linter](https://import-linter.readthedocs.io/) (`uv run lint-imports`) falha se algum import violar os contratos definidos no `pyproject.toml`.

### Decisões que valem saber

- **Nada é apagado.** O `DELETE` desativa o registro (`deleted_at`), e as leituras ignoram os desativados. O service expõe só métodos que respeitam essa regra, e o Protocol do controller não oferece o hard delete.
- **Os aliases de DI usam `X: TypeAlias = ...`, e não `type X = ...`.** O Litestar não reconhece o `SkipValidation` dentro de um alias `type`. Os detalhes estão nos comentários do `pyproject.toml`.
- **Os módulos de cadastro usam o service do Advanced Alchemy.** Módulos com cálculos pesados (cota, P&L, rentabilidade) devem ter uma camada de domínio em Python puro, testável sem banco.

## Como este projeto está sendo construído

O objetivo do projeto é **aprender**, não só entregar. Por isso, o código da aplicação é escrito **à mão**, com uma IA (Claude Code) no papel de **tutor**, e não de gerador de código. As regras ficam no `AGENTS.md`, que o Claude Code lê no início de cada sessão.

**O que o tutor faz:**

- explica conceitos (ORM, injeção de dependência, camadas, generics) e aponta a documentação;
- propõe a arquitetura e divide o trabalho em exercícios;
- revisa o código escrito, rodando `ruff`, `ty`, `lint-imports` e testes reais contra um banco temporário;
- explica os erros e faz perguntas que levam à correção, em vez de entregar a correção pronta;
- dá exemplos curtos (de 2 a 5 linhas) em **outro domínio**, para que precisem ser adaptados e não copiados.

**O que o tutor não faz:**

- escrever funções, rotas ou regras de negócio da aplicação.

A exceção são as **ferramentas e a configuração** (`pyproject.toml`, ruff, ty, import-linter, layout do projeto), a documentação e as operações de git. O tutor cuida dessas partes diretamente, porque não são o foco do aprendizado.

**O ciclo de cada exercício:**

1. o tutor explica o conceito e descreve a tarefa;
2. o desenvolvedor escreve o código;
3. o tutor revisa, roda as checagens e testa o comportamento real (por exemplo, a resposta HTTP para cada entrada);
4. o tutor aponta os problemas com o "porquê" de cada um, e o desenvolvedor corrige;
5. os passos 3 e 4 se repetem até tudo passar, e então segue-se para o próximo exercício.

**A sequência até aqui:** configuração do banco → plugin → `app.py` → model → repository e service → regra de negócio (SKU) → schema → controller → router → listagem paginada → extração das dependências (`deps.py`) → `PATCH` com `UNSET` e validação → `DELETE` → pytest → soft delete → API pública (`public.py`) → import-linter → migração do domínio para o de uma gestora.

## Status

Em andamento (WIP).

**Roteiro:**

- [x] renomear `catalog` → `instruments` e `orders` → `trades`
- [x] remodelar o ativo: código CETIP, tipo do ativo (enum com `CHECK` no banco); o preço sai do cadastro
- [ ] módulo de preços (série temporal por ativo e data)
- [x] módulo `trades` (operações), consumindo `instruments` pelo `public.py`
- [ ] eventos de domínio emitidos pelo `trades`
- [ ] módulo `positions` (posições e P&L), alimentado por eventos, com tabelas próprias
- [ ] contrato `layers` no import-linter

**Backlog**, em ordem de valor para um projeto real:

- [ ] schemas de resposta (`InstrumentRead`, `TradeRead`): hoje as respostas serializam o model ORM, e colunas internas como `deleted_at` aparecem no contrato
- [ ] **contract-first** (avaliar depois da POC, quando o front-end que substitui o Streamlit começar). Ver a seção "Contract-first" abaixo
- [ ] migrations com Alembic
- [ ] exceções de domínio e exception handlers
- [ ] testes de um módulo isolado, com fakes dos Protocols públicos
- [ ] registro de módulos (cada módulo se registra sozinho no app)
- [ ] usuários, autenticação e trilha de auditoria (quem alterou o quê)
- [ ] listeners idempotentes e padrão Outbox
- [ ] jobs em background (importação de preços, cálculo de cota)
- [ ] PostgreSQL (o destino final), com os testes rodando contra um PostgreSQL de verdade (por exemplo, com testcontainers). O SQLite se comporta diferente em alguns pontos: o `LIKE` dele ignora maiúsculas e minúsculas, e o do PostgreSQL não

## Contract-first (em avaliação)

Hoje a API é **code-first**: o Litestar gera o OpenAPI a partir dos `Struct`s e dos handlers (`uv run litestar --app litestar_sandbox.app:create_app schema openapi --output openapi.json`). A proposta é passar a **contract-first** quando houver um front-end em outra linguagem consumindo a API.

**O fluxo proposto:**

1. `contracts/openapi.yaml` é a fonte da verdade, revisada em PR por quem implementa e por quem consome (ou escrita em [TypeSpec](https://typespec.io/), que compila para OpenAPI).
2. Os `Struct`s do msgspec são **gerados** a partir dele com o [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) (`--output-model-type msgspec.Struct --use-annotated`) e nunca editados à mão.
3. O front-end gera o cliente TypeScript e um servidor mock ([Prism](https://github.com/stoplightio/prism)) a partir do mesmo arquivo.
4. O CI compara o OpenAPI gerado pela API com o contrato ([oasdiff](https://github.com/oasdiff/oasdiff)) e roda testes de contrato ([Schemathesis](https://schemathesis.readthedocs.io/)).

**O que um teste com o datamodel-code-generator mostrou:**

- ✅ `enum` vira `StrEnum`; `minLength`, `maxLength`, `pattern` e `exclusiveMinimum` (em inteiros) viram `msgspec.Meta`.
- ✅ Campos opcionais viram `X | UnsetType = UNSET`, e campos nullable ganham `| None`: a semântica do `PATCH` é preservada.
- ❌ `format: date` saiu como `str`, e não como `datetime.date`, com as opções padrão. É preciso descobrir a configuração certa.
- ⚠️ Regras que o JSON Schema não expressa (como "decimal maior que zero") não são geradas e vão para o service. É uma separação razoável: o schema cuida da forma dos dados, e o service das regras.

**Os custos:** um passo a mais em cada mudança (editar o contrato, gerar e implementar), YAML verboso, e a comparação entre o contrato escrito e o gerado pelo Litestar precisa ser semântica, porque os dois nunca ficam idênticos.

**O próximo passo sugerido:** migrar um módulo (o `instruments`) para `Struct`s gerados, com o oasdiff no CI, antes de adotar para todos.
