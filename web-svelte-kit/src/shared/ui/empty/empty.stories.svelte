<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./empty.svelte";
  import Header from "./empty-header.svelte";
  import Media from "./empty-media.svelte";
  import Title from "./empty-title.svelte";
  import Description from "./empty-description.svelte";
  import { Search } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/Empty",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="w-80">
      <Header>
        <Media variant="icon"><Search /></Media>
        <Title>Nenhum resultado</Title>
        <Description>Ajuste os filtros e tente de novo.</Description>
      </Header>
    </Root>
  {/snippet}
</Story>
