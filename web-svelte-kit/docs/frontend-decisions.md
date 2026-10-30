# Decisões de frontend — por quê

Este documento registra o raciocínio por trás das escolhas técnicas do `web-svelte-kit`, não só o que foi escolhido. Objetivo: quando alguém (humano ou agente) for mexer numa tela nova, dá pra consultar aqui o porquê de um padrão existir, em vez de just copiar o que já tem sem saber se é intencional. É um documento vivo — cresce conforme novas decisões forem tomadas.

## Contexto: três fronts em paralelo

O repositório tem três implementações de front (`web/`, `web-next/`, `web-svelte-kit/`) consumindo a mesma API Litestar. Isso não é indecisão — foi uma exploração deliberada para comparar stacks num projeto real antes de comprometer o time com uma. `web-svelte-kit` é o que está em desenvolvimento ativo no momento.

Diferença estrutural importante: `web/` é servido pela própria API via `litestar-vite` (same-origin, sem CORS). `web-next/` e `web-svelte-kit/` são processos à parte, falando com a API por HTTP cross-origin — por isso a API precisa de `CORSConfig` (`app.py`) e por isso o form de boletas usa Superforms em modo `SPA: true` em vez do fluxo "clássico" com `+page.server.ts` (não existe backend do SvelteKit no meio, só o browser chamando a API Litestar direto).

## Estrutura: Feature-Sliced Design

`src/app`, `src/pages`, `src/shared` seguem FSD. Cada slice (`instruments`, `trades`, `positions`) tem seus próprios `api/` e `ui/`, e só se comunica com outro slice através do `index.ts` dele — mesmo princípio do "só importa via `public.py`" que já vale pros módulos do backend (ver `AGENTS.md`). A vantagem concreta: dá pra apagar ou reescrever a tela de `trades` inteira sem tocar em `positions`, porque a única coisa que um importa do outro é o que está exportado deliberadamente no `index.ts`.

`shared/ui` é onde moram os componentes de design system (ver seção shadcn-svelte abaixo) — nunca específicos de uma tela.

## Design system base: shadcn-svelte + bits-ui

Em vez de uma biblioteca de componentes pronta (Material, Carbon, etc.), usamos shadcn-svelte: os componentes (`Button`, `Card`, `Select`, `Tooltip`...) são gerados via CLI (`npx shadcn-svelte add <componente>`) e **copiados pro repo** (`src/shared/ui/<componente>/`), não instalados como dependência de node_modules. Motivo: em cima de `bits-ui` (primitivas acessíveis sem estilo), o componente final é nosso código — dá pra editar, recolorir, remover partes, sem brigar com a API de uma lib externa nem esperar ela suportar o que falta. O custo é manter essas cópias atualizadas manualmente, mas pra um design system interno isso é aceitável: queremos controle, não a versão mais nova toda semana.

Os tokens de cor (`--background`, `--primary`, `--sidebar`, etc. em `app.css`) são o tema padrão do shadcn-svelte (`baseColor: neutral` em `components.json`), com claro e escuro já definidos — só faltava o toggle (ver seção de tema).

## Forms: Superforms + Formsnap + zod

Avaliadas: shadcn-svelte forms (que por baixo já é isso), Formsnap sozinho, TanStack Form.

Escolhido **Superforms + Formsnap + zod**:
- **zod** é o schema de validação: um arquivo `schema.ts` por formulário, validação roda no client (não tem backend do SvelteKit pra validar no servidor aqui — ver nota de CORS acima).
- **Superforms** dá o estado do form (`$formData`, erros, campo "tainted" etc.) de um jeito que funciona tanto com form actions do SvelteKit quanto em modo puramente client-side (`SPA: true`), que é o nosso caso.
- **Formsnap** é a camada de componentes (`Form.Field`, `Form.Control`, `Form.FieldErrors`) que liga o estado do Superforms à acessibilidade (`aria-describedby`, `aria-invalid`, ids) sem escrever isso à mão em cada campo.

**TanStack Form** ficou de fora: é headless e agnóstico de framework, o que significa escrever a camada de markup/acessibilidade do zero pra cada campo — exatamente o trabalho que Formsnap já resolve pronto em cima do Superforms. Pra um time que vai replicar o mesmo padrão de form em várias telas, ter o componente de campo já pronto (e padronizado) vale mais que a flexibilidade extra do TanStack.

Padrão a seguir em formulário novo: 1 schema zod, `superForm(..., { SPA: true, validators: zod4(schema) })`, campos sempre via `Form.Field`/`Form.Control`/`Form.FieldErrors` — nunca `<input>` cru fora disso.

## Gráficos: layerchart

Única lib avaliada até agora com integração nativa Svelte 5 + d3 madura o suficiente pro que precisávamos (séries temporais com eixo de data). É pré-1.0 (v2.9.2) e sua documentação assume que o app define um conjunto de CSS custom properties (`--color-surface-100`, `--color-surface-content`, etc.) que o shadcn-svelte não usa — isso causou dois bugs visuais reais (eixo com letras grossas/coladas e tooltip de hover branco-sobre-branco no dark) até mapearmos esses tokens pros nossos (`--popover`, `--muted-foreground`) em `app.css`. Isso é o tipo de atrito que vale documentar: quem adicionar um novo gráfico com layerchart e ver algo ilegível no dark mode, a causa provável é uma variável `--color-surface-*` que falta mapear, não um bug do componente.

Alternativas não avaliadas a fundo ainda: Chart.js (imperativo, não é Svelte-first), ECharts (mais pesado, mais voltado a dashboards densos). Fica como próximo passo se layerchart não aguentar um gráfico mais complexo (ex. candlestick, múltiplas séries facetadas).

## Layout: sidebar colapsável, tema, loading, tooltips

Decisões recentes, direcionadas por "menos cara de POC":

- **Sidebar colapsável** em vez de header com abas: estado (colapsado/expandido) em `localStorage`, ícone + tooltip quando recolhida. Escolhida colapsável em vez de fixa simples porque aproxima mais do padrão de app profissional (tipo Linear/Vercel) que o time quer como referência, mesmo custando um componente a mais pra manter.
- **Tema claro/escuro**: toggle na topbar, preferência em `localStorage`, aplicado via script bloqueante em `app.html` antes do primeiro paint (sem isso, pisca no tema errado por uma fração de segundo a cada carregamento).
- **`shared/ui/loading`**: um spinner padronizado único, pra nunca mais ter um "Carregando…" em texto solto (ou, pior, uma tela em branco) espalhado pelas telas.
- **`shared/ui/info-tooltip`**: ícone de informação + tooltip no hover, substituindo as `CardDescription` que só explicavam uma regra de negócio (ex. "O ativo é validado pelo instruments.public."). Regra seguida: texto que é *dado* (contagem de itens, etc.) continua visível; texto que é só *explicação* vira tooltip.

## Em aberto

Modais, botões e o resto da biblioteca de componentes padronizados ainda não foram desenhados — próximo passo combinado com o time.
