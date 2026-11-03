<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Progress from "./progress.svelte";

  const { Story } = defineMeta({
    title: "UI/Progress",
    component: Progress,
    tags: ["autodocs"],
    argTypes: {
      value: { control: { type: "range", min: 0, max: 100 } },
      max: { control: "number" },
    },
    args: { value: 65, max: 100 },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Progress {...args} class="w-64" />
  {/snippet}
</Story>
