<script lang="ts">
  import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";
  import type { Snippet } from "svelte";

  import "../app.css";
  import { configureApiClient } from "#shared/api/index.ts";
  import { auth } from "#shared/auth/index.ts";
  import AcrylicBackdrop from "../layout/AcrylicBackdrop.svelte";
  import Shell from "../layout/Shell.svelte";
  import SignIn from "../layout/SignIn.svelte";
  import { Loading, TooltipProvider } from "#shared/ui/index.ts";
  import { Toasts } from "#shared/ui/toast/index.ts";

  let { children }: { children: Snippet } = $props();

  configureApiClient();

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });

  // só no cliente: SSR renderiza "carregando" até o MSAL processar o retorno do redirect
  $effect(() => {
    auth.init();
  });

  // ao sair, nada do usuário anterior fica no cache
  $effect(() => {
    if (auth.account === null) {
      queryClient.clear();
    }
  });
</script>

<QueryClientProvider client={queryClient}>
  <TooltipProvider delayDuration={150}>
    <AcrylicBackdrop />
    {#if auth.account === undefined}
      <div class="flex h-screen items-center justify-center">
        <Loading />
      </div>
    {:else if auth.account === null}
      <SignIn />
    {:else}
      <Shell>{@render children()}</Shell>
    {/if}
    <Toasts />
  </TooltipProvider>
</QueryClientProvider>
