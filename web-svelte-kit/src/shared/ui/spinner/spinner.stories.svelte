<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Spinner from "./spinner.svelte";

  const { Story } = defineMeta({
    title: "UI/Spinner",
    component: Spinner,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Spinner class="size-5" />
  {/snippet}
</Story>
