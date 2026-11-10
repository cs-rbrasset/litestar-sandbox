<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./dropdown-menu.svelte";
  import Trigger from "./dropdown-menu-trigger.svelte";
  import Content from "./dropdown-menu-content.svelte";
  import Label from "./dropdown-menu-label.svelte";
  import Group from "./dropdown-menu-group.svelte";
  import Item from "./dropdown-menu-item.svelte";
  import Separator from "./dropdown-menu-separator.svelte";
  import { Button } from "#shared/ui/button/index.ts";
  import { ChevronDown, Image, LogOut, Trash2 } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/DropdownMenu",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<!-- Menu da conta no cabeçalho (Shell.svelte): Label com nome/e-mail, separador, ações.
  O `variant="destructive"` do Item fica aqui como referência, embora o Shell não o use. -->
<Story name="Playground">
  {#snippet template()}
    <Root>
      <Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="outline">Conta<ChevronDown data-icon="inline-end" /></Button>
        {/snippet}
      </Trigger>
      <Content align="end" class="w-56">
        <Label class="font-normal">
          <span class="block truncate text-sm font-medium">Claudio Silva</span>
          <span class="block truncate text-xs text-muted-foreground">cs@rbrasset.com.br</span>
        </Label>
        <Separator />
        <Group>
          <Item><Image data-icon="inline-start" />Plano de fundo</Item>
          <Item><LogOut data-icon="inline-start" />Sair</Item>
        </Group>
        <Separator />
        <Item variant="destructive"><Trash2 data-icon="inline-start" />Arquivar ativo</Item>
      </Content>
    </Root>
  {/snippet}
</Story>
