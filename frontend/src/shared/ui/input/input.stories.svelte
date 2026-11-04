<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Input from "./input.svelte";

  const { Story } = defineMeta({
    title: "UI/Input",
    component: Input,
    tags: ["autodocs"],
    argTypes: {
      type: { control: "select", options: ["text", "number", "date", "email", "password"] },
      placeholder: { control: "text" },
      disabled: { control: "boolean" },
    },
    args: { type: "text", placeholder: "nome@exemplo.com", disabled: false },
  });
</script>

<Story name="Playground" />
