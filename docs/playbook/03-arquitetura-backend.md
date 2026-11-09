# 3. Arquitetura do backend

## Monólito modular, dois pacotes de primeiro nível

Dentro de `backend/api/`, a árvore é **flat, sem pacote wrapper**:

```
backend/api/
├── app.py            # monta o app, não conhece módulos individualmente
├── core/             # infraestrutura compartilhada — nunca importa de modules/
└── modules/
    ├── <modulo-a>/    # ex.: ativos, boletas, posicoes, notas [AJUSTAR]
    │   ├── models.py        # shim de re-export pro database/
    │   ├── enums.py         # shim, se tiver enum
    │   ├── repositories.py
    │   ├── services.py
    │   ├── controllers.py
    │   ├── deps.py
    │   ├── protocols.py
    │   ├── schemas.py
    │   ├── listeners.py     # se consumir evento
    │   ├── public.py        # só se outro módulo consumir este
    │   └── domain.py         # só se houver regra de negócio testável sem banco
    └── <modulo-b>/
```

Import-linter trata `core` e `modules` como `root_packages` — eles não têm uma raiz comum tipo `app`, então cada um é tratado como pacote de primeiro nível pros contratos.

## Regra central: módulo só importa outro pelo `public.py`

Um módulo nunca faz `from modules.outro.services import X` direto. Se precisa de algo de outro módulo, esse módulo expõe um `public.py` com a superfície permitida, e o import-linter tem um contrato `ignore_imports` liberando só esse caminho.

Módulo que ninguém mais consome (ainda) não precisa de `public.py` — não crie a superfície antes de alguém precisar dela.

Dois tipos de contrato no import-linter:

1. **Módulo isolado** (ninguém depende dele, ele não depende de ninguém): dois contratos `forbidden` espelhados.
2. **Módulo que consome outro só pelo `public.py`**: contrato `ignore_imports` liberando especificamente esse caminho.

Contrato novo entra **no mesmo commit** do módulo novo — não é um "depois eu formalizo".

## `core` nunca importa `modules`

A dependência é sempre módulo → core, nunca o contrário. `core` é infraestrutura (auth, eventos, storage, settings de banco) que não sabe nada de domínio de negócio.

## Sem FK entre módulos

Tabelas de módulos diferentes não têm foreign key entre si. O dado que um módulo precisa de outro é **copiado no registro** (ex.: nome do autor copiado de uma tabela de identidade no momento do save) ou **viaja num evento**. Isso é o que permite, no limite, quebrar um módulo pra outro serviço sem migração de schema dolorosa — e também é o que impede um agente de IA de "resolver rápido" com um `ForeignKey` que acopla dois domínios que deveriam ser independentes.

## Models SQLAlchemy moram em `database/`, não no módulo

`database/models/<área>/model.py` tem a classe ORM de verdade (e os enums que as colunas usam, em `enums.py` ao lado). Hoje a área tem o mesmo nome do módulo que a usa primeiro, mas isso é coincidência de uso, não regra — a ideia é que `database` possa ser consumido por mais de um módulo ou mais de um serviço no futuro.

Dentro do módulo, `models.py` (e `enums.py`, se tiver) é **só um shim de re-export**:

```python
# backend/api/modules/<modulo>/models.py
from database.models.<area>.model import X
```

O resto do módulo (`services.py`, `controllers.py`, `repositories.py`) importa de `models.py` **local**, sem saber que é um re-export — isso mantém o módulo desacoplado de saber onde o model "realmente" mora, caso isso mude.

## Descoberta automática de rotas (`litestar-autowire`)

`app.py` não importa módulo nenhum. O autowire descobre:

- Classes `Controller` em `controllers.py` de cada módulo.
- Classes `EventListener` em `listeners.py` de cada módulo.

Cada controller declara seu próprio `path` (`/ativos`, `/boletas`, ...). Criar um módulo novo não exige tocar em `app.py` — é a mesma lógica de "menos lugar pra esquecer de atualizar" do capítulo 2.

## Arquivos por módulo — quando criar cada um

| Arquivo | Sempre existe? | Quando |
|---|---|---|
| `models.py` | Sim | Shim pro `database/`. |
| `repositories.py` | Sim | Acesso a dado, herda repository do Advanced Alchemy. |
| `services.py` | Sim | Regra de aplicação, herda `SQLAlchemyAsyncRepositoryService`. |
| `controllers.py` | Sim | Rotas HTTP. |
| `deps.py` | Sim | Provedores de DI do módulo. |
| `protocols.py` | Sim | Interfaces pra DI tipado (`Protocol`). |
| `schemas.py` | Sim | `msgspec.Struct` de request/response. |
| `listeners.py` | Só se consumir evento | Handler de evento publicado por `core/events.py`. |
| `public.py` | Só se outro módulo consumir este | Superfície explícita liberada pro import-linter. |
| `domain.py` | Só se houver regra de negócio testável sem banco | Lógica pura, sem I/O — vale a pena isolar quando dá pra testar sem fixture de banco. |

## Isolamento por dono (quando o recurso é "por pessoa")

Quando um recurso é visível só pro dono (cada pessoa só vê o próprio), toda rota responde **404, não 403**, pra quem não é dono — nunca revela que o recurso existe pra quem não deveria saber disso. O identificador estável de pessoa (role de banco, claim de token — depende de como a auth do repo funciona, ver capítulo 5) nunca é montado a partir de texto vindo do usuário.
