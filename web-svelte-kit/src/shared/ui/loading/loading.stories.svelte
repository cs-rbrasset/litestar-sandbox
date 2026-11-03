<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Loading from "./loading.svelte";

  const { Story } = defineMeta({
    title: "UI/Loading",
    component: Loading,
    tags: ["autodocs"],
    argTypes: {
      label: { control: "text" },
      size: { control: "select", options: ["sm", "md", "lg"] },
    },
    args: { label: "Carregando…", size: "md" },
  });
</script>

<Story name="Playground" />
