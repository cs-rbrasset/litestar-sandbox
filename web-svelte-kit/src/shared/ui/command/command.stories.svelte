<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./command.svelte";
  import CmdInput from "./command-input.svelte";
  import List from "./command-list.svelte";
  import Empty from "./command-empty.svelte";
  import Group from "./command-group.svelte";
  import Item from "./command-item.svelte";

  const { Story } = defineMeta({
    title: "UI/Command",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="w-72 rounded-md border border-border">
      <CmdInput placeholder="Buscar comando..." />
      <List>
        <Empty>Nada encontrado.</Empty>
        <Group heading="Sugestões">
          <Item>Nova boleta</Item>
          <Item>Novo ativo</Item>
        </Group>
      </List>
    </Root>
  {/snippet}
</Story>
