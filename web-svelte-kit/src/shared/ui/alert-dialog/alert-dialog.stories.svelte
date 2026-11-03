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
      open: { control: "boolean" },
    },
    args: { open: false },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root open={args.open}>
      <Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="destructive">Excluir</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Header>
          <Title>Confirmar exclusão?</Title>
          <Description>Essa ação não pode ser desfeita.</Description>
        </Header>
        <Footer>
          <Cancel>Voltar</Cancel>
          <Action variant="destructive">Excluir</Action>
        </Footer>
      </Content>
    </Root>
  {/snippet}
</Story>
