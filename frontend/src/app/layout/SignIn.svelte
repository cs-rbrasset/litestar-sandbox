<script lang="ts">
  import { auth } from "#shared/auth/index.ts";
  import { Button } from "#shared/ui/index.ts";
</script>

<div class="flex min-h-screen items-center justify-center px-6">
  <div class="flex w-full max-w-sm flex-col items-center gap-8 text-center">
    <img src="/logo-rbr.svg" alt="RBR Asset" class="h-10 w-auto dark:brightness-0 dark:invert" />

    <div class="flex flex-col gap-2">
      <h1 class="text-lg font-semibold">Gestão de ativos, boletas e posições</h1>
      <p class="text-muted-foreground text-sm">
        Workspaces de instrumentos, boletas e posições num só sistema.
      </p>
    </div>

    <Button type="button" onclick={auth.signIn} class="w-full">Entrar com Microsoft</Button>
  </div>
</div>
