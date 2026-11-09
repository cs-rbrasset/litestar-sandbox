# 13. Trabalhando com agentes de IA

## `AGENTS.md` como contrato operacional

Todo repo que segue este padrão deveria ter um `AGENTS.md` na raiz — não como documentação opcional, mas como o documento que um agente de IA lê automaticamente antes de agir no repo. Ele deve conter, no mínimo:

- Estrutura do repositório (versão curta do capítulo 2 deste playbook).
- Comandos de gate obrigatórios (capítulo 8) — sem ambiguidade de "roda isso antes de considerar pronto".
- Arquitetura resumida (capítulo 3) — o suficiente pra um agente não violar a fronteira de módulo na primeira tentativa.
- Convenções de código específicas que um linter não pega sozinho (capítulo 7) — ex. a regra de `SkipValidation` + `TypeAlias`, que é fácil de "corrigir" errado se só olhar o warning do ruff.
- Checklists (capítulos 9 e 10) copiados ou referenciados diretamente — um agente segue checklist explícito melhor que prosa solta.

Este playbook é o material de referência "por que é assim"; o `AGENTS.md` é o resumo operacional "faça assim". Os dois devem concordar — se um mudar, o outro precisa ser revisado.

## Modo tutor vs. modo implementação, por branch

Um padrão útil (usado neste próprio repo) é diferenciar o que um agente pode fazer **sozinho** por branch:

- **Branch(es) de modo tutor** (ex. branch principal, branch de uma feature sensível em andamento): agente explica, revisa, sugere diff — não escreve a implementação direto no código.
- **Branch(es) de modo implementação liberado**: agente escreve função completa, módulo novo, refatoração, teste, sem precisar de aprovação linha a linha.

Isso vai declarado explicitamente no topo do `AGENTS.md`, nomeando as branches por nome (não "branch principal" genérico) — um agente lendo o arquivo precisa saber, sem ambiguidade, se a branch em que está autoriza ele a implementar ou só a tutorar.

## Por que restrição verificável > prosa

As regras mais importantes deste playbook (contrato de import-linter, proibição de FK entre módulo, `404` em vez de `403`, os três gates obrigatórios) têm uma coisa em comum: **são verificáveis por uma ferramenta**, não só por review humano lendo o diff.

Isso importa duplamente com agente de IA no loop: um agente segue regra expressa em prosa com variação (interpretação, esquecimento ao longo de uma sessão longa); uma regra que falha o `pytest` ou o `lint-imports` é factual — ou passa ou não passa. Ao desenhar uma convenção nova pro repo, prefira sempre que possível **codificar a regra em algo que quebra o build**, em vez de só documentar e confiar em disciplina.

## Memória entre sessões

Se o ambiente de agente usado suportar memória persistente entre conversas (perfil do usuário, feedback acumulado, contexto de projeto), trate isso como complementar ao `AGENTS.md`, não substituto: `AGENTS.md` é a fonte de verdade versionada e visível a qualquer agente/dev que abra o repo; memória de sessão é contexto adicional específico de quem está operando o agente naquele momento (preferência de estilo de resposta, decisão recente ainda não documentada formalmente).

## Quando uma decisão de arquitetura nova aparece

Se, durante uma sessão de implementação, um agente (ou dev) toma uma decisão estrutural nova que quebra ou estende uma regra deste playbook (ex.: um módulo que *precisa* de FK com outro por razão genuína, uma exceção ao padrão de evento), **o commit que introduz a exceção deveria atualizar o playbook/AGENTS.md no mesmo PR** — não deixar a exceção implícita no código pra alguém descobrir depois lendo o diff.
