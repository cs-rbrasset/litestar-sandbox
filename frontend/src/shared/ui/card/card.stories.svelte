<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./card.svelte";
  import Header from "./card-header.svelte";
  import Title from "./card-title.svelte";
  import Description from "./card-description.svelte";
  import Content from "./card-content.svelte";

  const { Story } = defineMeta({
    title: "UI/Card",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="w-64">
      <Header>
        <Title>Título</Title>
        <Description>Descrição curta</Description>
      </Header>
      <Content class="text-sm">Conteúdo.</Content>
    </Root>
  {/snippet}
</Story>
