# 11. Banco de dados e migrations

## Estado atual: `create_all`, sem Alembic ainda

Hoje o schema do banco compartilhado (ex. Postgres gerenciado) é mantido com `create_all=True` do SQLAlchemy — isso **só cria tabela que ainda não existe**. Isso tem uma implicação crítica:

> **Mudou uma tabela que já existe no banco compartilhado? `create_all` não altera.** Reiniciar a API sozinho não corrige nada. Sem um `ALTER TABLE` manual (ex. via conexão direta com `asyncpg`, a mesma sessão que você usaria pra inspecionar o banco), a API sobe sem erro mas quebra em runtime pra quem estiver testando contra aquele banco.

Esse passo manual é responsabilidade de quem faz a mudança — não pule, mesmo que pareça "só mais uma coluna".

Antes de assumir que é `create_all` puro, **confira se já existe `alembic/` ou alguma migration no repo** — isso é um estado transitório, não a arquitetura final, e pode já ter mudado.

## Handoff planejado (Alembic + privilégio restrito)

O plano documentado prevê:

1. Migrations via Alembic substituindo `create_all` como fonte de verdade do schema.
2. Troca da conexão de uma role de superusuário/owner (ex. `postgres`) pra uma role de aplicação com privilégio restrito de verdade (ex. `app_login`), seguindo o princípio de menor privilégio.

Enquanto esse handoff não for aplicado, trate `create_all` como o estado real, não como detalhe implementado errado — é uma decisão consciente de estágio do projeto, documentada, com um plano de saída definido.

## Models moram em `database/`, migration (quando existir) deveria morar junto

Quando o handoff pra Alembic acontecer, a convenção natural é a migration morar no mesmo pacote `database/` onde já moram os models — não espalhada dentro de `backend/api/`, pela mesma razão de `database/` ser o pacote dono do schema.
