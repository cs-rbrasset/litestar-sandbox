<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./dropdown-menu.svelte";
  import Trigger from "./dropdown-menu-trigger.svelte";
  import Content from "./dropdown-menu-content.svelte";
  import Group from "./dropdown-menu-group.svelte";
  import Item from "./dropdown-menu-item.svelte";
  import Separator from "./dropdown-menu-separator.svelte";
  import { Button } from "#shared/ui/button/index.ts";
  import { Mail, Settings, Trash2 } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/DropdownMenu",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root>
      <Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="outline">Ações ▾</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Group>
          <Item><Settings data-icon="inline-start" />Configurações</Item>
          <Item><Mail data-icon="inline-start" />Enviar email</Item>
        </Group>
        <Separator />
        <Item variant="destructive"><Trash2 data-icon="inline-start" />Excluir</Item>
      </Content>
    </Root>
  {/snippet}
</Story>
