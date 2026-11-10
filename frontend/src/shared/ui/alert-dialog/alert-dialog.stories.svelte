<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./alert-dialog.svelte";
  import Trigger from "./alert-dialog-trigger.svelte";
  import Content from "./alert-dialog-content.svelte";
  import Header from "./alert-dialog-header.svelte";
  import Title from "./alert-dialog-title.svelte";
  import Description from "./alert-dialog-description.svelte";
  import Footer from "./alert-dialog-footer.svelte";
  import Cancel from "./alert-dialog-cancel.svelte";
  import Action from "./alert-dialog-action.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/AlertDialog",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      open: { control: "boolean", description: "Força o diálogo aberto (útil para inspecionar o conteúdo)." },
    },
    args: { open: false },
  });
</script>

<!-- Toda ação destrutiva passa por aqui (AGENTS.md): Trigger no botão, Action destructive dispara
  a ação de verdade. Mesmo texto do cancelamento de boleta em Trades.svelte. -->
<Story name="Playground">
  {#snippet template(args)}
    <Root open={args.open}>
      <Trigger>
        {#snippet child({ props })}
          <Button {...props} size="sm" variant="ghost">Cancelar</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Header>
          <Title>Cancelar boleta #42?</Title>
          <Description>Essa ação não pode ser desfeita.</Description>
        </Header>
        <Footer>
          <Cancel>Voltar</Cancel>
          <Action variant="destructive">Cancelar boleta</Action>
        </Footer>
      </Content>
    </Root>
  {/snippet}
</Story>
