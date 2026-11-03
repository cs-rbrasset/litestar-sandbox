<script lang="ts">
  import type { Snippet } from "svelte";

  import { Image, LogOut } from "@lucide/svelte";

  import { auth } from "#shared/auth/index.ts";
  import {
    Avatar,
    AvatarFallback,
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuSubTrigger,
    DropdownMenuTrigger,
    ThemeToggle,
    WallpaperPicker,
  } from "#shared/ui/index.ts";
  import Sidebar from "./Sidebar.svelte";

  let { children }: { children: Snippet } = $props();

  let accountLabel = $derived(auth.account?.name ?? auth.account?.username ?? "");
  let accountInitials = $derived(
    accountLabel
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join(""),
  );
</script>

<div class="flex h-screen">
  <Sidebar />

  <div class="flex min-h-0 min-w-0 flex-1 flex-col">
    <header
      class="bg-background/60 flex h-14 shrink-0 items-center justify-end gap-3 border-b border-border px-6 backdrop-blur-xl backdrop-saturate-150"
    >
      <ThemeToggle />
      {#if auth.account}
        <DropdownMenu>
          <DropdownMenuTrigger>
            {#snippet child({ props })}
              <Avatar {...props} size="sm" class="cursor-pointer">
                <AvatarFallback>{accountInitials}</AvatarFallback>
              </Avatar>
            {/snippet}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-56">
            <DropdownMenuLabel class="font-normal">
              <span class="block truncate text-sm font-medium">{accountLabel}</span>
              {#if auth.account.username && auth.account.username !== accountLabel}
                <span class="block truncate text-xs text-muted-foreground">{auth.account.username}</span>
              {/if}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Image class="size-4" />
                Plano de fundo
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent class="w-44 p-2">
                <WallpaperPicker />
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuSeparator />
            <DropdownMenuItem onclick={auth.signOut}>
              <LogOut class="size-4" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      {/if}
    </header>

    <main class="min-h-0 flex-1 overflow-y-auto px-6 py-8">
      {@render children()}
    </main>
  </div>
</div>
