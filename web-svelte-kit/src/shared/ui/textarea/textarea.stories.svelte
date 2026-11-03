<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Textarea from "./textarea.svelte";

  const { Story } = defineMeta({
    title: "UI/Textarea",
    component: Textarea,
    tags: ["autodocs"],
    argTypes: {
      placeholder: { control: "text" },
      disabled: { control: "boolean" },
      rows: { control: "number" },
    },
    args: { placeholder: "Observações...", disabled: false, rows: 3 },
  });
</script>

<Story name="Playground" />
