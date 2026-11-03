<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./dialog.svelte";
  import Trigger from "./dialog-trigger.svelte";
  import Content from "./dialog-content.svelte";
  import Header from "./dialog-header.svelte";
  import Title from "./dialog-title.svelte";
  import Description from "./dialog-description.svelte";
  import Footer from "./dialog-footer.svelte";
  import Close from "./dialog-close.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Dialog",
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
          <Button {...props} variant="outline">Abrir dialog</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Header>
          <Title>Editar perfil</Title>
          <Description>Conteúdo arbitrário — formulário, texto, o que precisar.</Description>
        </Header>
        <Footer>
          <Close>
            {#snippet child({ props })}
              <Button {...props} variant="outline">Cancelar</Button>
            {/snippet}
          </Close>
          <Button>Salvar</Button>
        </Footer>
      </Content>
    </Root>
  {/snippet}
</Story>
