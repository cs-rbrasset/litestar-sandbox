<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Separator from "./separator.svelte";

  const { Story } = defineMeta({
    title: "UI/Separator",
    component: Separator,
    tags: ["autodocs"],
    argTypes: {
      orientation: { control: "select", options: ["horizontal", "vertical"] },
    },
    args: { orientation: "vertical" },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <div class="flex h-10 items-center gap-4">
      <span>Item A</span>
      <Separator {...args} />
      <span>Item B</span>
    </div>
  {/snippet}
</Story>
