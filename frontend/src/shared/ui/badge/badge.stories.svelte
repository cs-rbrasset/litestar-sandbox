<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Badge from "./badge.svelte";

  const VARIANTS = ["default", "secondary", "destructive", "outline", "ghost", "link"] as const;

  // Mesmas classes de STATUS em Trades.svelte: o status da boleta sobrescreve a cor via `class`.
  const TRADE_STATUS = [
    { label: "Pendente", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" },
    { label: "Liquidada", className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" },
    { label: "Cancelada", className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300" },
  ];

  const { Story } = defineMeta({
    title: "UI/Badge",
    component: Badge,
    tags: ["autodocs"],
    argTypes: {
      variant: {
        control: "select",
        options: VARIANTS,
        description: "Estilo visual. Com `href` o badge vira um link (`<a>`).",
      },
      href: { control: "text", description: "Opcional: renderiza como `<a>` em vez de `<span>`." },
    },
    args: { variant: "default", href: undefined },
  });
</script>

<Story name="Playground">Pendente</Story>

<Story name="Variantes">
  {#snippet template()}
    <div class="flex flex-wrap items-center gap-2">
      {#each VARIANTS as variant (variant)}
        <Badge {variant}>Publicado</Badge>
      {/each}
    </div>
  {/snippet}
</Story>

<!-- Status de boleta, como na tabela de Trades.svelte. -->
<Story name="Status de boleta">
  {#snippet template()}
    <div class="flex flex-wrap items-center gap-2">
      {#each TRADE_STATUS as status (status.label)}
        <Badge class={status.className}>{status.label}</Badge>
      {/each}
    </div>
  {/snippet}
</Story>
