<script lang="ts">
  import { auth } from "#shared/auth/index.ts";
  import { Button } from "#shared/ui/index.ts";
</script>

<div class="flex min-h-screen items-center justify-center px-6">
  <div
    class="bg-card text-card-foreground ring-foreground/10 flex w-full max-w-sm flex-col gap-5 rounded-2xl p-8 shadow-sm ring-1"
  >
    <div>
      <p class="text-brand-600 text-xs font-semibold tracking-widest uppercase">POC SvelteKit</p>
      <h1 class="mt-1 text-xl font-semibold">Entrar</h1>
      <p class="text-muted-foreground mt-1 text-sm">
        Login via Entra ID direto no navegador (MSAL.js, PKCE) — o token nunca passa pelo
        backend, só é enviado pra API já pronto.
      </p>
    </div>
    <Button type="button" onclick={auth.signIn}>Entrar com Microsoft</Button>
  </div>
</div>
