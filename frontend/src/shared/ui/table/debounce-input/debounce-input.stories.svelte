<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import DebounceInput from "./debounce-input.svelte";

  const { Story } = defineMeta({
    title: "UI/DebounceInput",
    component: DebounceInput,
    tags: ["autodocs"],
    argTypes: {
      placeholder: { control: "text" },
      debounce: { control: "number" },
    },
    args: { placeholder: "Filtrar...", debounce: 300 },
  });
</script>

<Story name="Playground" />
