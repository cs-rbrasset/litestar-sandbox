# Playbook: repositórios "core" na RBR

Este playbook descreve o **padrão de arquitetura e de trabalho** usado em repositórios "core" da RBR — monólitos modulares em Python/Litestar com front-end SvelteKit separado, pensados tanto para devs humanos quanto para agentes de IA trabalharem neles.

Ele foi extraído do repositório `litestar-sandbox` (o primeiro repo a seguir esse padrão), mas é escrito como **template genérico**: qualquer repo novo que siga a mesma filosofia (monólito modular, workspace `uv`, módulos flat, eventos para desacoplar entre módulos, porta de jobs para trabalho longo) pode copiar esta pasta e ajustar os nomes.

Convenção de leitura: blocos marcados **[AJUSTAR]** são os pontos que mudam de repo pra repo (nomes de módulos, domínio de negócio, credenciais). O resto é o padrão em si.

## Sumário

1. [Visão geral e filosofia](01-visao-geral.md) — por que monólito modular, por que esse stack, quando este padrão não se aplica.
2. [Estrutura do repositório](02-estrutura-repo.md) — workspace `uv`, pastas, onde cada coisa mora.
3. [Arquitetura do backend](03-arquitetura-backend.md) — módulos, `core`, pacote `database`, import-linter, autowire.
4. [Eventos e jobs assíncronos](04-eventos-e-jobs.md) — porta de jobs (`core/jobs.py`), worker, e eventos só entre módulos.
5. [Autenticação e identidade](05-autenticacao.md) — Entra ID, verificador composto, espelhamento de role no Postgres.
6. [Front-end](06-frontend.md) — SvelteKit, Feature-Sliced Design, geração de client a partir do OpenAPI.
7. [Convenções de código](07-convencoes-codigo.md) — schemas, DI, services, datas, estilo.
8. [Testes e qualidade](08-testes-e-qualidade.md) — gates obrigatórios, fixtures, o que testar onde.
9. [Checklist: módulo novo no backend](09-checklist-modulo-novo.md)
10. [Checklist: tela nova no front](10-checklist-tela-nova.md)
11. [Banco de dados e migrations](11-banco-de-dados.md) — estado atual (`create_all`) e o handoff planejado pra Alembic.
12. [Git e fluxo de trabalho](12-git-e-fluxo.md) — commits, branches, o que nunca commitar.
13. [Trabalhando com agentes de IA](13-trabalhando-com-agentes-ia.md) — `AGENTS.md`, modo tutor vs. modo implementação, como orientar o agente por branch.
14. [Integrações externas](14-integracoes-externas.md) — gateways, parsers, arquivo bruto, storage, reprocessamento, scraping.
15. [Decisões em aberto](15-decisoes-em-aberto.md) — o que ainda não foi decidido, e por quem.

## Como usar isto num repo novo

1. Copie `docs/playbook/` inteiro pro repo novo.
2. Rode uma busca por **[AJUSTAR]** e resolva cada ponto (nome dos módulos, domínio, credenciais específicas).
3. Escreva (ou copie e adapte) um `AGENTS.md` na raiz do novo repo apontando pros mesmos princípios — ver capítulo 13.
4. Mantenha o playbook vivo: ele documenta decisão de arquitetura, não é só onboarding estático. Toda decisão estrutural nova (um módulo que quebra a regra de não ter FK entre módulos, por exemplo) deveria gerar uma atualização aqui, não só um comentário no código.
