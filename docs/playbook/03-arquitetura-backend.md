# 3. Arquitetura do backend

## Monólito modular, dois pacotes de primeiro nível

Dentro de `backend/api/`, a árvore é **flat, sem pacote wrapper**:

```
backend/api/
├── app.py            # monta o app, não conhece módulos individualmente
├── worker.py         # a outra metade do backend: serve os jobs (capítulo 4)
├── core/             # infraestrutura compartilhada — nunca importa de modules/
└── modules/
    ├── <modulo-a>/    # ex.: ativos, boletas, posicoes, notas [AJUSTAR]
    │   ├── models.py        # obrigatório — shim de re-export pro database/
    │   ├── services.py      # obrigatório
    │   ├── controllers.py   # obrigatório
    │   ├── schemas.py       # obrigatório
    │   └── ...              # o resto nasce sob demanda (ver tabela abaixo)
    └── <modulo-b>/
```

Import-linter trata `core`, `modules` e `database` como `root_packages` — eles não têm uma raiz comum tipo `app`, então cada um é tratado como pacote de primeiro nível pros contratos.

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

### Modelo canônico × ORM

Módulo que recebe dado de fora (de um custodiante, de um upload) tem **duas** representações, e elas não se confundem:

| | Onde | O que é |
|---|---|---|
| canônico | `modules/<modulo>/domain/` | `dataclass(frozen=True, slots=True)` ou `msgspec.Struct(frozen=True)`, sem dependência de banco. É o que o parser produz e o que o `public.py` aceita. |
| ORM | `database/models/<área>/` | a tabela. O `repositories.py` converte canônico → ORM. |
| contrato HTTP | `modules/<modulo>/schemas.py` | `msgspec.Struct` de request/response, e nada mais. |

Consequência da pureza: o `domain/` não pode importar `database`, e `database` não pode importar a API. Quando um vocabulário fechado (um `StrEnum`) é usado nos dois lados, a saída é **copiar e travar a cópia com teste** — o `StrEnum` é a fonte de verdade no `domain/`, o `database` guarda a lista de strings pro `CHECK`, e um teste compara as duas. Abrir uma das duas regras sairia mais caro.

## Descoberta automática de rotas (`litestar-autowire`)

`app.py` não importa módulo nenhum. O autowire descobre:

- Classes `Controller` em `controllers.py` de cada módulo.
- Classes `EventListener` em `listeners.py` de cada módulo.

Cada controller declara seu próprio `path` (`/ativos`, `/boletas`, ...). Criar um módulo novo não exige tocar em `app.py` — é a mesma lógica de "menos lugar pra esquecer de atualizar" do capítulo 2.

## Arquivos por módulo — obrigatórios e sob demanda

Quatro arquivos são obrigatórios. **Todo o resto nasce sob demanda** — arquivo vazio "pra seguir o padrão" é ruído que o próximo leitor vai tentar entender.

| Arquivo | Obrigatório? | Quando |
|---|---|---|
| `models.py` | **Sim** | Shim de re-export pro `database/`. Módulo sem tabela declara isso no lugar (ver `custodiante`). |
| `services.py` | **Sim** | Regra de aplicação. |
| `controllers.py` | **Sim** | Rotas HTTP. |
| `schemas.py` | **Sim** | `msgspec.Struct` de request/response. |
| `repositories.py` | Quando tem acesso a dado próprio | Herda repository do Advanced Alchemy, ou funções de query/upsert. |
| `deps.py` | Quando o módulo provê dependência | Provedores de DI. |
| `protocols.py` | Quando a DI é tipada por interface | `Protocol` do que o controller recebe. |
| `enums.py` | Quando tem enum | Shim do `database/`, ou vocabulário próprio se o módulo não tem tabela. |
| `domain/` (ou `domain.py`) | Quando há regra de negócio testável sem banco | Lógica pura, sem I/O. Vira pacote (`domain/`) quando cresce por subtipo. |
| `public.py` | Quando outro módulo consome este | Superfície explícita liberada pro import-linter. |
| `tasks.py` | Quando o módulo tem job | Jobs declarados com `@job` (capítulo 4). |
| `listeners.py` | Quando consome evento de outro módulo | Handler de evento publicado por `core/events.py`. |

Pastas aparecem pela mesma regra: `gateways/`, `parsers/`, `domain/` só existem quando há mais de um arquivo do tipo — ver o módulo `custodiante` (capítulo 14).

## O que entra no `core`

Critério, os dois ao mesmo tempo:

1. **É infraestrutura, sem regra de negócio** — autenticação, eventos, jobs, storage, settings, sessão de banco.
2. **É usado por pelo menos dois módulos** (ou pelo app e por um módulo).

Peça usada por um módulo só mora no módulo, mesmo parecendo genérica. Ela sobe pro `core` quando o segundo consumidor aparece — e aí a subida é um commit pequeno, não uma adivinhação feita cedo demais.

`core` nunca importa `modules`, e por isso nunca cita um módulo pelo nome: quando precisa varrer os módulos (a descoberta de jobs, por exemplo), recebe o **nome do pacote como string**, igual ao `domain_packages` do autowire.

## O pacote `database` é contrato público

`database` não é "a pasta dos models": é um pacote instalável próprio, publicado num PyPI privado e consumido por outros softwares da RBR. Isso tem consequências práticas:

- **Versionamento semântico.** Remover ou renomear coluna é mudança maior. Coluna nova opcional é menor.
- **Migrations versionadas junto com o pacote** — quem instala a versão N tem como chegar ao schema N.
- **Documentar quais áreas são estáveis** para uso externo e quais ainda se mexem.
- **Política de escrita externa**: preferir role só de leitura pra quem consome de fora; escrita passa pelo dono da área.
- **`database` não importa `core` nem `modules`**, e as dependências dele são mínimas (hoje: `advanced-alchemy`). Fiscalizado por contrato.

Proteções que acompanham isso:

| Proteção | Onde |
|---|---|
| cada módulo só importa a **própria área** de `database.models` | contrato do import-linter, um por área |
| FK nunca cruza área | teste no próprio pacote, varrendo o `MetaData` |
| `database` não depende da API nem do framework | contrato do import-linter |

## Contratos do import-linter

Configuração de sessão (no `pyproject.toml` de `backend/api`):

```toml
[tool.importlinter]
root_packages = ["core", "modules", "database"]
include_external_packages = true      # pra proibir pacote de terceiro (prefect, sqlalchemy...)
exclude_type_checking_imports = true  # import sob TYPE_CHECKING não existe em runtime
```

`database` entra como root package, e não como pacote externo, de propósito: como externo, a ferramenta só enxergaria o nome de topo e "cada módulo só importa a própria área" seria inexprimível.

Famílias de contrato em uso:

| Contrato | Forma |
|---|---|
| `core` não depende de `modules` | `forbidden` |
| `database` não depende da API nem do framework | `forbidden` |
| nenhum módulo importa o orquestrador (só `core.jobs`) | `forbidden` + `allow_indirect_imports` |
| módulo isolado (ninguém depende dele, ele não depende de ninguém) | dois `forbidden` espelhados |
| módulo que consome outro só pelo `public.py` | `forbidden` + `ignore_imports` nesse caminho |
| irmãos que não se conhecem | `independence` |
| `domain/` e `parsers/` são puros (sem banco, framework, rede, navegador) | `forbidden` listando os pacotes proibidos |
| cada módulo só importa a própria área de `database.models` | um `forbidden` por área |

`allow_indirect_imports = true` aparece onde o que importa é o **import direto** — o caminho indireto legítimo passa pelo `public.py` do dono ou pela porta do `core`.

## Convenções de nome

**[AJUSTAR: módulos no plural ou no singular]** — este playbook foi escrito com módulos no plural (`ativos`, `boletas`, `posicoes`, `notas`) e os módulos de integração nasceram no singular (`custodiante`, `carteira`, `extrato`). Escolher um e padronizar; até lá, não misture dentro do mesmo módulo.

**[AJUSTAR: idioma por camada]** — hoje convivem módulos com identificadores em inglês (`PositionService`, `positions_at`) e em português (`CarteiraService`, `registrar_carteira`). A convenção que faz sentido é domínio em português e vocabulário técnico em inglês, mas ela precisa ser decidida e aplicada; não troque o idioma de um módulo existente "de passagem".

## Localização dos testes

**[AJUSTAR]** — hoje os testes vivem numa árvore paralela (`backend/api/tests/modules/<modulo>/`). A alternativa é testes dentro do próprio módulo, que facilita extrair o módulo depois. Decidir antes que a quantidade de testes torne a migração cara.

## Descobrir o que o sistema montou sozinho

Duas coisas são descobertas por convenção e não aparecem em nenhuma lista: os controllers/listeners (autowire) e os jobs (`core.jobs.descobrir()`). **[AJUSTAR]** — vale um comando (ou um teste) que imprima tudo que foi descoberto, pra que "meu controller não subiu" seja uma pergunta respondível em um segundo. Hoje o autowire loga o resumo na subida e `core.jobs.descobrir()` é coberto por teste.

## Isolamento por dono (quando o recurso é "por pessoa")

Quando um recurso é visível só pro dono (cada pessoa só vê o próprio), toda rota responde **404, não 403**, pra quem não é dono — nunca revela que o recurso existe pra quem não deveria saber disso. O identificador estável de pessoa (role de banco, claim de token — depende de como a auth do repo funciona, ver capítulo 5) nunca é montado a partir de texto vindo do usuário.
