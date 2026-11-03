<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./menubar.svelte";
  import Menu from "./menubar-menu.svelte";
  import Trigger from "./menubar-trigger.svelte";
  import Content from "./menubar-content.svelte";
  import Item from "./menubar-item.svelte";
  import Separator from "./menubar-separator.svelte";

  const { Story } = defineMeta({
    title: "UI/Menubar",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root>
      <Menu>
        <Trigger>Arquivo</Trigger>
        <Content>
          <Item>Novo</Item>
          <Separator />
          <Item>Sair</Item>
        </Content>
      </Menu>
    </Root>
  {/snippet}
</Story>
