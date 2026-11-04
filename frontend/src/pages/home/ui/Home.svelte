<script lang="ts">
  import { Image as ImageIcon, ShieldCheck, Sparkles } from "@lucide/svelte";

  import { auth } from "#shared/auth/index.ts";
  import {
    Avatar,
    AvatarFallback,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    WallpaperPicker,
  } from "#shared/ui/index.ts";

  const now = new Date();
  const greeting = now.getHours() < 12 ? "Bom dia" : now.getHours() < 18 ? "Boa tarde" : "Boa noite";
  const today = (() => {
    const formatted = new Intl.DateTimeFormat("pt-BR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(now);
    return formatted.charAt(0).toUpperCase() + formatted.slice(1);
  })();

  let accountLabel = $derived(auth.account?.name ?? auth.account?.username ?? "");
  let firstName = $derived(accountLabel.split(/\s+/)[0] ?? "");
  let accountInitials = $derived(
    accountLabel
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join(""),
  );
</script>

<div class="mx-auto flex max-w-4xl flex-col gap-6">
  <div class="bg-card ring-foreground/10 relative overflow-hidden rounded-2xl p-8 ring-1 backdrop-blur-xl backdrop-saturate-150">
    <Sparkles class="text-brand-500/15 absolute -top-8 -right-8 size-40" />
    <p class="text-brand-600 relative text-xs font-semibold tracking-widest uppercase">{today}</p>
    <h1 class="relative mt-2 text-3xl font-semibold tracking-tight md:text-4xl">{greeting}, {firstName}</h1>
    <p class="text-muted-foreground relative mt-2 max-w-md text-sm">
      Bem-vindo de volta. Acompanhe seu perfil e personalize o visual do sistema por aqui.
    </p>
  </div>

  <div class="grid gap-6 md:grid-cols-2">
    <Card>
      <CardHeader>
        <CardTitle>Perfil</CardTitle>
        <CardDescription>Conta usada para entrar no sistema.</CardDescription>
      </CardHeader>
      <CardContent class="flex items-center gap-4">
        <Avatar size="lg" class="ring-brand-500/30 ring-2">
          <AvatarFallback class="text-base">{accountInitials}</AvatarFallback>
        </Avatar>
        <div class="min-w-0">
          <p class="truncate text-sm font-medium">{accountLabel}</p>
          {#if auth.account?.username && auth.account.username !== accountLabel}
            <p class="text-muted-foreground truncate text-xs">{auth.account.username}</p>
          {/if}
          <p class="text-muted-foreground mt-1.5 flex items-center gap-1 text-xs">
            <ShieldCheck class="size-3.5" />
            Conectado via Entra ID
          </p>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <ImageIcon class="size-4" />
          Plano de fundo
        </CardTitle>
        <CardDescription>Escolha a textura acrílica do sistema.</CardDescription>
      </CardHeader>
      <CardContent>
        <WallpaperPicker showLabels class="gap-3 sm:grid-cols-3" />
      </CardContent>
    </Card>
  </div>
</div>
