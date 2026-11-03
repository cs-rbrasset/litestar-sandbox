<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Toggle from "./toggle.svelte";

  const { Story } = defineMeta({
    title: "UI/Toggle",
    component: Toggle,
    tags: ["autodocs"],
    argTypes: {
      variant: { control: "select", options: ["default", "outline"] },
      size: { control: "select", options: ["default", "sm", "lg"] },
      pressed: { control: "boolean" },
      disabled: { control: "boolean" },
    },
    args: { variant: "default", size: "default", pressed: false, disabled: false },
  });
</script>

<Story name="Playground">B</Story>
