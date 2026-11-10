<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import DebounceInput from "./debounce-input.svelte";

  const { Story } = defineMeta({
    title: "UI/DebounceInput",
    component: DebounceInput,
    tags: ["autodocs"],
    argTypes: {
      value: { control: "text", description: "Valor já debounced. No app é `bind:value` no filtro global da tabela." },
      placeholder: { control: "text" },
      debounce: { control: "number", description: "Espera em ms antes de propagar o valor (Trades usa 200)." },
    },
    args: { value: "", placeholder: "Filtrar boletas...", debounce: 200, class: "max-w-56" },
  });
</script>

<!-- Filtro rápido da tabela de boletas (Trades.svelte). O X limpa o campo assim que há texto. -->
<Story name="Playground" />
