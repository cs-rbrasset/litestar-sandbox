<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Loading from "./loading.svelte";

  const SIZES = ["sm", "md", "lg"] as const;

  const { Story } = defineMeta({
    title: "UI/Loading",
    component: Loading,
    tags: ["autodocs"],
    argTypes: {
      label: { control: "text", description: "Texto ao lado do spinner. Vazio mostra só o ícone (como no +layout)." },
      size: { control: "select", options: SIZES, description: "Tamanho do spinner." },
    },
    args: { label: "Carregando boletas", size: "md" },
  });
</script>

<Story name="Playground" />

<Story name="Tamanhos">
  {#snippet template()}
    <div class="flex items-center gap-6">
      {#each SIZES as size (size)}
        <Loading {size} label={size} class="py-0" />
      {/each}
    </div>
  {/snippet}
</Story>
