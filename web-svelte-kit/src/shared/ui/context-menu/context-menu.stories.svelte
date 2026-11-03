<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./context-menu.svelte";
  import Trigger from "./context-menu-trigger.svelte";
  import Content from "./context-menu-content.svelte";
  import Item from "./context-menu-item.svelte";

  const { Story } = defineMeta({
    title: "UI/ContextMenu",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root>
      <Trigger class="flex h-20 w-64 items-center justify-center rounded-md border border-dashed border-border text-sm text-muted-foreground">
        Clique com o botão direito aqui
      </Trigger>
      <Content>
        <Item>Copiar</Item>
        <Item>Colar</Item>
      </Content>
    </Root>
  {/snippet}
</Story>
