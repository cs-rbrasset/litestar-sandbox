<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./scroll-area.svelte";
  import Scrollbar from "./scroll-area-scrollbar.svelte";

  const { Story } = defineMeta({
    title: "UI/ScrollArea",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="h-32 w-64 rounded-md border border-border p-4">
      <div class="flex flex-col gap-2 text-sm">
        {#each Array(12) as _, i (i)}
          <p>Linha {i + 1}</p>
        {/each}
      </div>
      <Scrollbar orientation="vertical" />
    </Root>
  {/snippet}
</Story>
