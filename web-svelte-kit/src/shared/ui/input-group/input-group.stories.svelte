<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import { Search } from "@lucide/svelte";

  import Root from "./input-group.svelte";
  import Addon from "./input-group-addon.svelte";
  import GroupInput from "./input-group-input.svelte";

  const { Story } = defineMeta({
    title: "UI/InputGroup",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="w-64">
      <Addon><Search /></Addon>
      <GroupInput placeholder="Buscar..." />
    </Root>
  {/snippet}
</Story>
