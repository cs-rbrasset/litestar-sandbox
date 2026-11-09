# 8. Testes e qualidade

## Os três gates, sempre, mesmo pra mudança pequena

Dentro de `backend/api/`, antes de qualquer commit:

```bash
uv run pytest
uv run ruff check .
uv run lint-imports
```

Os três — não "só rodei o pytest porque era um typo". `lint-imports` é o que garante que a fronteira entre módulos (capítulo 3) não foi furada; `ruff` pega estilo e alguns bugs óbvios; `pytest` é o óbvio.

## Setup de teste

- Testes de API usam SQLite, **um arquivo por teste**, em `tmp_path` — isolamento total entre testes, sem precisar de transação/rollback manual.
- Fixtures centrais em `backend/api/tests/conftest.py` (ex.: `app_client`, que já manda token de autenticação de teste).
- Teste que depende de comportamento específico do Postgres (ex. `FOR UPDATE` / lock de linha) é **pulado automaticamente** quando o banco do teste é SQLite — SQLite não suporta a mesma semântica de lock.

## O que testar onde

- **Comportamento novo vem com teste no mesmo commit.** Não é "depois eu escrevo".
- Lógica de domínio pura (sem I/O) é testada sem banco — é exatamente pra isso que existe `domain.py` dentro de um módulo (capítulo 3): se a lógica está lá, o teste não precisa de fixture de banco nenhuma.
- Recurso por dono (só o dono vê) precisa de **pelo menos um teste de isolamento entre duas pessoas diferentes** — confirmando que a pessoa B recebe 404 (não 403) ao tentar acessar recurso da pessoa A.

## Por que 404 e não 403 é parte do teste

Retornar 403 pra quem não é dono revela que o recurso existe (só que "você não pode"). 404 não revela nada. O teste de isolamento deve checar o status code exato, não só "deu erro".
