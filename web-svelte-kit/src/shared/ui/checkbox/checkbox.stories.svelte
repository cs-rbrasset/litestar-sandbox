<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Checkbox from "./checkbox.svelte";

  const { Story } = defineMeta({
    title: "UI/Checkbox",
    component: Checkbox,
    tags: ["autodocs"],
    argTypes: {
      checked: { control: "boolean" },
      disabled: { control: "boolean" },
    },
    args: { checked: true, disabled: false },
  });
</script>

<Story name="Playground" />
