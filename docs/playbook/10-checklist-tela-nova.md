# 10. Checklist: tela nova no front

1. **Endpoint novo no backend primeiro, API rodando com ele** (reinicie o processo — um servidor com reload automático às vezes não pega controller novo sozinho), **depois** regere os tipos a partir do OpenAPI. Sem isso, os hooks de data fetching não têm o que chamar.

2. **Estrutura FSD**: `src/pages/<feature>/{ui,api,index.ts}`; a rota só importa de `#pages/<feature>/index.ts` e renderiza — nenhuma lógica na rota.

3. **`api/<feature>.ts`**: query/mutation recebendo uma função reativa (`() => ({...})`), não um objeto direto. Toda chamada do SDK gerado passa pelo wrapper de unwrap. **Toda mutation leva `onError` notificando o usuário** — sem isso, uma falha de verdade fica muda.

4. **Componente shadcn só se importa pela barrel** — nunca do caminho interno do componente. O lint de FSD recusa esse sidestep. Componente que ainda não está na barrel entra lá no mesmo commit que passa a usá-lo.

5. **Two-way binding usa `bind:`** (`bind:value`, `bind:checked`, `bind:pressed`) — é o padrão do resto do app. Não trocar por controlado + `onChange` mesmo que o componente aceite os dois — já causou bug real.

6. **Prefira ação explícita (botão) a autosave** via efeito reativo disparando a cada digitação/toggle. Se o pedido for autosave de verdade, teste contra a API rodando de verdade antes de considerar pronto, não só o typecheck.

7. **Depois de qualquer mudança**: `npm run typecheck` e `npm run lint:fsd`, sempre — e teste contra a API real quando o typecheck sozinho não prova que o fluxo funciona.

8. Dev server com `EPERM` em tipos gerados? Limpar a pasta de build do SvelteKit e reiniciar resolve (corrida de arquivo com outro processo, ex. `svelte-check` em paralelo).
