<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Badge from "./badge.svelte";

  const { Story } = defineMeta({
    title: "UI/Badge",
    component: Badge,
    tags: ["autodocs"],
    argTypes: {
      variant: {
        control: "select",
        options: ["default", "secondary", "destructive", "outline", "ghost", "link"],
      },
    },
    args: { variant: "default" },
  });
</script>

<Story name="Playground">Pendente</Story>
