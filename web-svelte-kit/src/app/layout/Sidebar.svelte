<script lang="ts">
  import { page } from "$app/state";
  import { API_URL } from "$app/env/public";
  import { ExternalLink, PanelLeft, PanelLeftClose, PieChart, Receipt, Warehouse } from "@lucide/svelte";

  import { cn } from "#shared/lib/utils.ts";
  import { Button, Tooltip, TooltipContent, TooltipTrigger } from "#shared/ui/index.ts";

  const STORAGE_KEY = "sidebar-collapsed";

  const NAV = [
    { href: "/", label: "Ativos", icon: Warehouse },
    { href: "/boletas", label: "Boletas", icon: Receipt },
    { href: "/posicoes", label: "Posições", icon: PieChart },
  ] as const;

  let collapsed = $state(typeof localStorage !== "undefined" && localStorage.getItem(STORAGE_KEY) === "1");

  function toggle() {
    collapsed = !collapsed;
    localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
  }
</script>

<aside
  class={cn(
    "flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-200",
    collapsed ? "w-16" : "w-56",
  )}
>
  <div class={cn("flex h-14 items-center border-b border-sidebar-border px-3", collapsed && "justify-center px-0")}>
    {#if !collapsed}
      <span class="truncate text-sm font-semibold tracking-wide">RBR Asset</span>
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
    <Button variant="ghost" size="icon" onclick={toggle} aria-label={collapsed ? "Expandir menu" : "Recolher menu"}>
      {#if collapsed}
        <PanelLeft class="size-4" />
      {:else}
        <PanelLeftClose class="size-4" />
      {/if}
    </Button>
  </div>
</aside>
