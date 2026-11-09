# 6. Front-end

## Stack e por que é processo separado

SvelteKit, rodando via Vite dev server, **processo à parte da API** — sem front same-origin. A API tem CORS explícito (`CORSConfig`) liberando só a origem de dev do front. Isso mantém a API "pura": ela não serve HTML nem assets, e pode ser consumida por qualquer cliente que fale HTTP, não só esse front.

Já existiram ports em outros frameworks (React, Next.js) nalgum momento da vida do projeto — descartados depois de comparação direta. Isso é decisão de arquitetura registrada, não acidente: não revisitar sem motivo novo.

## Feature-Sliced Design (FSD)

O front segue FSD. Pontos que mais importam no dia a dia:

- `src/pages/<feature>/{ui,api,index.ts}` — a lógica de cada feature mora aqui.
- A rota (`src/app/routes/.../+page.svelte`) **só importa de `#pages/<feature>/index.ts` e renderiza** — zero lógica na rota em si.
- Componente shadcn-svelte só se importa pela barrel (`#shared/ui/index.ts`), nunca do caminho interno do componente. Há um lint próprio pra isso (`npm run lint:fsd`) que recusa esse sidestep.

## Geração de tipos a partir do OpenAPI

`npm run generate-types` lê o schema direto de `/api/v1/schema/openapi.json` da API rodando. Isso significa:

1. **Precisa da API rodando com o endpoint novo já no ar** antes de gerar — e reiniciada (um servidor com reload automático às vezes não pega controller novo sozinho; confirmar).
2. O client TypeScript (hooks TanStack Query) não é escrito à mão — é gerado. Mudar o schema do backend sem regenerar deixa o front com tipos desatualizados, não com erro de compilação necessariamente.

## Padrão de data fetching

- `createQuery`/`createMutation` do TanStack Query recebendo uma **função reativa** (`() => ({...})`), não um objeto direto — é assim que o resto do app relê props reativamente (ex. um `id` que muda).
- Toda chamada ao SDK gerado passa por um wrapper de unwrap (que normaliza erro/sucesso).
- **Toda mutation tem `onError` notificando o usuário.** Sem isso, uma falha de rede ou de validação fica muda — parece que "não salvou nada" sem explicação nenhuma pro usuário. Isso já causou confusão real em sessão de desenvolvimento; é regra, não sugestão.

## Two-way binding

Usa `bind:value`/`bind:checked`/`bind:pressed` — não o padrão `value` controlado + `onChange` mesmo quando o componente aceita os dois. Trocar por controlado já causou bug real (estado do componente não refletia o próprio valor).

## Autosave: cuidado

Prefira ação explícita (botão "Salvar") a autosave reagindo a toda digitação via efeito reativo. Debounce dentro de um efeito reativo é fácil de acertar na superfície e errar na prática — já gerou um loop infinito de requisições numa sessão real. Se o pedido for autosave de verdade, **testar contra a API rodando de verdade**, não só confiar no typecheck.

## Ações destrutivas sempre confirmadas

Toda exclusão (de qualquer entidade) passa por um diálogo de confirmação antes de executar — nunca um `onclick` direto num botão de deletar/cancelar/arquivar. Padrão: trigger no botão, ação destrutiva de verdade só dispara dentro da confirmação.

## Storybook: só componente em uso de verdade

A biblioteca de componentes shadcn-svelte (`frontend/src/shared/ui/`) tem dezenas de componentes prontos, mas o Storybook só mostra story de componente **usado de fato em alguma página**. Regra prática:

- Componente passa a ser usado numa página pela primeira vez → o mesmo commit cria a story dele.
- Componente para de ser usado em qualquer página → a story dele sai junto.

Isso evita Storybook virando catálogo de "componente que existe mas ninguém usa", que fica desatualizado silenciosamente.

## Checklist de verificação depois de qualquer mudança

- `npm run typecheck`
- `npm run lint:fsd`
- Teste contra API real (curl nos endpoints, ou dev server) sempre que o typecheck sozinho não prova que o fluxo funciona (mutations, navegação, efeitos).

## Problema conhecido do dev server

`EPERM` em arquivos de tipo gerado (`.svelte-kit/types/...`) pode acontecer por corrida de arquivo com outro processo escrevendo ao mesmo tempo (ex. `svelte-check` rodando em paralelo). Limpar a pasta de build do SvelteKit e reiniciar o dev server resolve.
