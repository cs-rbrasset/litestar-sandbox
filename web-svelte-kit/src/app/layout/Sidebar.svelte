<script lang="ts">
  import { page } from "$app/state";
  import { API_URL } from "$app/env/public";
  import {
    BookOpen,
    ExternalLink,
    Home,
    Pin,
    PinOff,
    PieChart,
    Receipt,
    StickyNote,
    Warehouse,
  } from "@lucide/svelte";

  import { cn } from "#shared/lib/utils.ts";
  import { Button, Tooltip, TooltipContent, TooltipTrigger } from "#shared/ui/index.ts";

  const STORAGE_KEY = "sidebar-pinned";

  const NAV = [
    { href: "/", label: "Início", icon: Home },
    { href: "/ativos", label: "Ativos", icon: Warehouse },
    { href: "/boletas", label: "Boletas", icon: Receipt },
    { href: "/posicoes", label: "Posições", icon: PieChart },
    { href: "/notepad", label: "Notepad", icon: StickyNote },
    { href: "/wiki", label: "Wiki", icon: BookOpen },
  ] as const;

  // Fixada: reserva espaço, sempre expandida. Sem fixar: vira um rail de ícones que
  // expande por cima do conteúdo (sem empurrar layout) só enquanto o mouse/foco estão nela.
  let pinned = $state(typeof localStorage !== "undefined" && localStorage.getItem(STORAGE_KEY) === "1");
  let hovering = $state(false);
  let expanded = $derived(pinned || hovering);
  let collapsed = $derived(!expanded);

  function togglePin() {
    pinned = !pinned;
    localStorage.setItem(STORAGE_KEY, pinned ? "1" : "0");
  }

  function onFocusOut(event: FocusEvent) {
    const next = event.relatedTarget as Node | null;
    if (!next || !(event.currentTarget as HTMLElement).contains(next)) {
      hovering = false;
    }
  }
</script>

<div
  class={cn("relative h-screen shrink-0 transition-[width] duration-200", pinned ? "w-56" : "w-16")}
  onmouseenter={() => (hovering = true)}
  onmouseleave={() => (hovering = false)}
  onfocusin={() => (hovering = true)}
  onfocusout={onFocusOut}
  role="none"
>
  <aside
    class={cn(
      "flex h-screen flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground backdrop-blur-xl backdrop-saturate-150 transition-[width] duration-200",
      pinned ? "w-56" : cn("absolute left-0 top-0 z-20", expanded ? "w-56 shadow-lg" : "w-16"),
    )}
  >
    <div class={cn("flex h-14 items-center border-b border-sidebar-border px-3", collapsed && "justify-center px-0")}>
      {#if !collapsed}
        <img src="/logo-rbr.svg" alt="RBR Asset" class="h-6 w-auto dark:brightness-0 dark:invert" />
      {/if}
    </div>

    <nav class="flex flex-1 flex-col gap-1 p-2" aria-label="Navegação principal">
      {#each NAV as item (item.href)}
        {@const active = page.url.pathname === item.href}
        {@const Icon = item.icon}
        {#if collapsed}
          <Tooltip>
            <TooltipTrigger>
              {#snippet child({ props })}
                <a
                  {...props}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  class={cn(
                    "flex items-center justify-center rounded-md p-2.5 text-sm transition-colors",
                    active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon class="size-4.5" />
                </a>
              {/snippet}
            </TooltipTrigger>
            <TooltipContent side="right">{item.label}</TooltipContent>
          </Tooltip>
        {:else}
          <a
            href={item.href}
            aria-current={active ? "page" : undefined}
            class={cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            <Icon class="size-4.5" />
            {item.label}
          </a>
        {/if}
      {/each}
    </nav>

    <div class={cn("flex items-center gap-1 border-t border-sidebar-border p-2", collapsed ? "flex-col" : "justify-between")}>
      <Tooltip>
        <TooltipTrigger>
          {#snippet child({ props })}
            <a
              {...props}
              href={`${API_URL}/api/v1/schema/swagger`}
              target="_blank"
              rel="noreferrer"
              class="flex items-center justify-center rounded-md p-2 text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            >
              <ExternalLink class="size-4" />
            </a>
          {/snippet}
        </TooltipTrigger>
        <TooltipContent side="right">Documentação da API</TooltipContent>
      </Tooltip>
      <Button variant="ghost" size="icon" onclick={togglePin} aria-label={pinned ? "Desafixar menu" : "Fixar menu"}>
        {#if pinned}
          <PinOff class="size-4" />
        {:else}
          <Pin class="size-4" />
        {/if}
      </Button>
    </div>
  </aside>
</div>
