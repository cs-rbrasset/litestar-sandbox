<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Button from "./button.svelte";
  import { Plus, Trash2 } from "@lucide/svelte";

  const VARIANTS = ["default", "outline", "secondary", "ghost", "destructive", "link"] as const;
  const SIZES = ["xs", "sm", "default", "lg"] as const;
  const ICON_SIZES = ["icon-xs", "icon-sm", "icon", "icon-lg"] as const;

  const { Story } = defineMeta({
    title: "UI/Button",
    component: Button,
    tags: ["autodocs"],
    argTypes: {
      variant: {
        control: "select",
        options: VARIANTS,
        description: "Estilo visual. `destructive` é reservado para ações irreversíveis (arquivar, cancelar boleta).",
      },
      size: {
        control: "select",
        options: [...SIZES, ...ICON_SIZES],
        description: "Altura e padding. Os `icon-*` são quadrados, para botões só com ícone.",
      },
      disabled: { control: "boolean", description: "Desabilita e reduz a opacidade (ex.: enquanto a mutation está pendente)." },
    },
    args: { variant: "default", size: "default", disabled: false },
  });
</script>

<Story name="Playground">Registrar boleta</Story>

<!-- Todas as variantes lado a lado, no tamanho padrão. -->
<Story name="Variantes">
  {#snippet template()}
    <div class="flex flex-wrap items-center gap-2">
      {#each VARIANTS as variant (variant)}
        <Button {variant}>Liquidar</Button>
      {/each}
    </div>
  {/snippet}
</Story>

<!-- Tamanhos de texto e os quadrados de ícone. Botão só com ícone leva aria-label. -->
<Story name="Tamanhos">
  {#snippet template()}
    <div class="flex flex-col gap-4">
      <div class="flex flex-wrap items-center gap-2">
        {#each SIZES as size (size)}
          <Button {size}><Plus data-icon="inline-start" />Novo ativo</Button>
        {/each}
      </div>
      <div class="flex flex-wrap items-center gap-2">
        {#each ICON_SIZES as size (size)}
          <Button {size} variant="outline" aria-label="Arquivar ativo"><Trash2 /></Button>
        {/each}
      </div>
    </div>
  {/snippet}
</Story>

<!-- Estado desabilitado: mesmo uso de Trades.svelte enquanto a transição está pendente. -->
<Story name="Desabilitado" args={{ disabled: true }}>Liquidar</Story>
