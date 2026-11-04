<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Switch from "./switch.svelte";

  const { Story } = defineMeta({
    title: "UI/Switch",
    component: Switch,
    tags: ["autodocs"],
    argTypes: {
      checked: { control: "boolean" },
      disabled: { control: "boolean" },
    },
    args: { checked: true, disabled: false },
  });
</script>

<Story name="Playground" />
