<script lang="ts">
  import { page } from "$app/state";
  import { API_URL } from "$app/env/public";
  import type { Snippet } from "svelte";

  import { auth } from "#shared/auth/index.ts";
  import { Button } from "#shared/ui/index.ts";

  let { children, name }: { children: Snippet; name: string } = $props();

  const STEPS = [
    { href: "/", label: "Ativos", hint: "Cadastro por código CETIP" },
    { href: "/boletas", label: "Boletas", hint: "Registro e liquidação" },
    { href: "/posicoes", label: "Posições", hint: "Posição do fundo na data" },
  ] as const;

</script>

<div class="min-h-screen">
  <header class="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
    <div class="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-6 pt-6">
      <div class="pb-4">
        <p class="text-xs font-semibold tracking-widest text-brand-600 uppercase">POC SvelteKit</p>
        <h1 class="text-xl font-semibold">Do ativo à posição</h1>
      </div>
      <nav class="flex gap-1" aria-label="Etapas do fluxo">
        {#each STEPS as s, index (s.href)}
          {@const active = page.url.pathname === s.href}
          <a
            href={s.href}
            aria-current={active ? "page" : undefined}
            class={`flex items-center gap-2 border-b-2 px-4 pb-3 text-sm transition-colors ${
              active
                ? "border-brand-600 font-medium text-slate-900 dark:text-white"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
            title={s.hint}
          >
            <span
              class={`flex size-5 items-center justify-center rounded-full text-[11px] ${
                active ? "bg-brand-600 text-white" : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
              }`}
            >
              {index + 1}
            </span>
            {s.label}
          </a>
        {/each}
      </nav>
      <div class="mb-3 flex items-center gap-3">
        <span class="text-sm text-slate-500">{name}</span>
        <Button variant="ghost" size="sm" onclick={auth.signOut}>Sair</Button>
      </div>
    </div>
  </header>

  <main class="mx-auto max-w-6xl px-6 py-8">
    {@render children()}
  </main>

  <footer class="mx-auto max-w-6xl px-6 pb-8 text-xs text-slate-500">
    API em <a class="underline" href={`${API_URL}/api/v1/schema/swagger`}>/api/v1/schema</a> · cliente
    gerado do OpenAPI, direto do endpoint da API (sem litestar-vite)
  </footer>
</div>
