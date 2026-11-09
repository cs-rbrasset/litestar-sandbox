# 1. Visão geral e filosofia

## O problema que esse padrão resolve

Times pequenos (poucos devs, agentes de IA fazendo boa parte da implementação) precisam de um meio-termo entre:

- **Microsserviços cedo demais**: overhead de infra, deploy e contratos de rede antes de o domínio estar entendido o suficiente pra desenhar essas fronteiras direito.
- **Monólito sem fronteira nenhuma**: tudo importa tudo, qualquer mudança em um canto quebra outro, e um agente de IA (ou um dev novo) não tem como saber o que é seguro tocar sem ler o repo inteiro.

A resposta é **monólito modular**: um único processo/deploy, mas módulos com fronteira de import real (não só convenção de pasta) entre eles. Cada módulo é "quase um microsserviço" — tem sua própria camada de repository/service/controller — mas sem rede, sem serialização entre módulos, sem deploy separado.

## Por que isso importa pra agentes de IA especificamente

Um agente de IA trabalhando num monólito sem fronteiras tende a:

- Importar direto de um módulo pro outro porque "dá pra resolver assim", introduzindo acoplamento invisível.
- Criar FK entre tabelas de módulos diferentes porque é o caminho de menor resistência no SQLAlchemy.
- Não saber que uma mudança de schema precisa de teste de isolamento entre usuários, porque nada força isso.

As regras deste playbook (contratos de import-linter, proibição de FK entre módulos, checklists obrigatórios) existem **especificamente pra dar ao agente um conjunto de restrições verificáveis automaticamente** (`lint-imports`, `pytest`, `ruff`) em vez de depender só de boa vontade ou de review humano pegar tudo.

## Peças do stack e por que cada uma foi escolhida

| Peça | Escolha | Por quê |
|---|---|---|
| Gerenciador de pacotes Python | `uv` com workspace | Dois+ pacotes Python (API e `database`) compartilhando lockfile, sem duplicar dependência, com `database` podendo virar pacote instalável à parte depois. |
| Framework web | Litestar | DI tipado, DTO/validação via msgspec, plugins (SQLAlchemy, eventos, autowire) que casam com o padrão modular. |
| Descoberta de rotas | `litestar-autowire` | Elimina um `app.py` que precisa saber de todo módulo novo — reduz o "lugar errado pra esquecer de atualizar". |
| Fronteira entre módulos | import-linter (contratos `forbidden`/`ignore_imports`) | Fronteira é enforced em CI, não só documentada. |
| Validação/schema | `msgspec.Struct` | Mais rápido que Pydantic, integra nativo com Litestar DTO. |
| Models SQLAlchemy | pacote `database/` separado, fora da API | Pensado pra virar instalável à parte (outro serviço/worker lendo o mesmo schema sem depender da API). |
| Job longo | Prefect self-hosted, via evento + listener | Controller não acopla com client do Prefect; troca de orquestrador fica isolada no listener do módulo. |
| Auth | Entra ID (MSAL.js no front, resource-server no back) | Front é cliente público, zero segredo no servidor pro login; backend só valida JWT contra JWKS. |
| Front-end | SvelteKit + Feature-Sliced Design | Processo separado da API (sem same-origin), FSD dá fronteira de import no front espelhando a fronteira de módulo no back. |

## Quando este padrão NÃO se aplica

- Protótipo descartável / spike de uma tarde: overhead de contrato de import-linter e checklist não compensa.
- Domínio com um único "módulo" óbvio e sem previsão de crescer: comece simples, adote o padrão modular quando o segundo módulo aparecer.
- Equipe grande o suficiente pra microsserviços reais fazerem sentido (times donos de serviço, deploy independente necessário): este padrão é o degrau antes disso, não substituto permanente.

## Modo tutor vs. modo implementação (contexto de agente de IA)

Branches podem ter regras diferentes pra até onde um agente de IA pode ir sozinho:

- **Modo tutor** (ex.: branch principal, branch de uma feature em andamento sensível): agente explica e revisa, não escreve a implementação.
- **Modo implementação liberado** (ex.: branch dedicada pra isso): agente pode escrever função completa, módulo novo, refatoração, teste.

Isso vive no `AGENTS.md` do repo (ver capítulo 13), não é uma regra deste playbook — mas o playbook assume que, quando liberado, o agente segue as mesmas regras de arquitetura que um dev humano seguiria.
