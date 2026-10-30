<script lang="ts">
  import type { Snippet } from "svelte";

  import { auth } from "#shared/auth/index.ts";
  import { Button, ThemeToggle } from "#shared/ui/index.ts";
  import Sidebar from "./Sidebar.svelte";

  let { children, name }: { children: Snippet; name: string } = $props();
</script>

<div class="flex h-screen">
  <Sidebar />

  <div class="flex min-w-0 flex-1 flex-col">
    <header class="flex h-14 shrink-0 items-center justify-end gap-3 border-b border-border px-6">
      <ThemeToggle />
      <span class="text-sm text-muted-foreground">{name}</span>
      <Button variant="ghost" size="sm" onclick={auth.signOut}>Sair</Button>
    </header>

    <main class="flex-1 overflow-y-auto px-6 py-8">
      {@render children()}
    </main>
  </div>
</div>
