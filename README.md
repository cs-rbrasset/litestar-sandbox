# litestar-sandbox

Sandbox para aprender [Litestar](https://docs.litestar.dev/) construindo um **monólito modular** com SQLite e [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/).

## Como rodar

Requisito: [uv](https://docs.astral.sh/uv/). Ele instala o Python 3.14 e as dependências sozinho.

```bash
uv sync
uv run litestar --app litestar_sandbox.app:app run --reload
```

- API: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/schema/swagger>

O banco é um arquivo `sandbox.db` criado no diretório onde você roda o comando, com as tabelas geradas no startup. Para usar outro banco, defina a variável `DATABASE_URL`:

```bash
DATABASE_URL="sqlite+aiosqlite:///./outro.db" uv run litestar --app litestar_sandbox.app:app run
```

### Endpoints

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/ping` | health check |
| POST | `/catalog/products` | cria um produto (o SKU é normalizado para maiúsculas, sem espaços nas pontas) |
| GET | `/catalog/products/{id}` | busca um produto por id |

### Qualidade

```bash
uv run ruff check src      # lint
uv run ruff format src     # formatação
uv run ty check src        # checagem de tipos
```

## Arquitetura

Cada módulo de `modules/` é dono dos seus dados e expõe só um router (e, no futuro, o seu service) pelo `__init__.py`. O `app.py` não conhece os detalhes internos de nenhum módulo.

```text
src/litestar_sandbox/
├── app.py                  # cria o app e registra os routers dos módulos
├── core/
│   └── database.py         # config do SQLAlchemy e plugin, compartilhados
└── modules/
    ├── catalog/
    │   ├── __init__.py     # fachada pública: catalog_router
    │   ├── controllers.py  # HTTP
    │   ├── schemas.py      # validação de entrada (msgspec)
    │   ├── services.py     # regras de negócio
    │   ├── repositories.py # acesso a dados
    │   └── models.py       # tabelas
    └── orders/             # próximo módulo
```

Uma requisição percorre as camadas nesta ordem: controller → service → repository → model.

## Como este projeto está sendo construído

O objetivo do projeto é **aprender**, não só entregar. Por isso, o código da aplicação é escrito **à mão**, com uma IA (Claude Code) no papel de **tutor**, e não de gerador de código. As regras ficam no `AGENTS.md`, que o Claude Code lê no início de cada sessão.

**O que o tutor faz:**

- explica conceitos (ORM, injeção de dependência, camadas, generics) e aponta a documentação;
- propõe a arquitetura e divide o trabalho em exercícios;
- revisa o código escrito, rodando `ruff`, `ty` e testes reais contra um banco temporário;
- explica os erros e faz perguntas que levam à correção, em vez de entregar a correção pronta;
- dá exemplos curtos (de 2 a 5 linhas) em **outro domínio**, para que precisem ser adaptados e não copiados.

**O que o tutor não faz:**

- escrever funções, rotas ou regras de negócio da aplicação.

A exceção são as **ferramentas e a configuração** (`pyproject.toml`, ruff, ty, layout do projeto) e a documentação. O tutor cuida dessas partes diretamente, porque não são o foco do aprendizado.

**O ciclo de cada exercício:**

1. o tutor explica o conceito e descreve a tarefa;
2. o desenvolvedor escreve o código;
3. o tutor revisa, roda as checagens e testa o comportamento real (por exemplo, a resposta HTTP para cada entrada);
4. o tutor aponta os problemas com o "porquê" de cada um, e o desenvolvedor corrige;
5. os passos 3 e 4 se repetem até tudo passar, e então segue-se para o próximo exercício.

**A sequência até aqui:** configuração do banco → plugin → `app.py` → model → repository e service → regra de negócio (SKU) → schema → controller → router.

## Status

Em andamento (WIP). Próximos passos:

- [ ] `GET /catalog/products` (listagem)
- [ ] `PATCH` e `DELETE` de produtos
- [ ] módulo `orders`, referenciando produtos sem acoplar os módulos
- [ ] testes com pytest
