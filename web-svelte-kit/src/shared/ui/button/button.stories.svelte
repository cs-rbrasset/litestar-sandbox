<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Button from "./button.svelte";

  const { Story } = defineMeta({
    title: "UI/Button",
    component: Button,
    tags: ["autodocs"],
    argTypes: {
      variant: {
        control: "select",
        options: ["default", "outline", "secondary", "ghost", "destructive", "link"],
      },
      size: {
        control: "select",
        options: ["default", "xs", "sm", "lg", "icon", "icon-xs", "icon-sm", "icon-lg"],
      },
      disabled: { control: "boolean" },
    },
    args: { variant: "default", size: "default", disabled: false },
  });
</script>

<Story name="Playground">Registrar boleta</Story>
