<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Skeleton from "./skeleton.svelte";

  const { Story } = defineMeta({
    title: "UI/Skeleton",
    component: Skeleton,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <div class="flex flex-col gap-2">
      <Skeleton class="h-4 w-48" />
      <Skeleton class="h-4 w-32" />
    </div>
  {/snippet}
</Story>
