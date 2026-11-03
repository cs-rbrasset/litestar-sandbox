<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./sheet.svelte";
  import Trigger from "./sheet-trigger.svelte";
  import Content from "./sheet-content.svelte";
  import Header from "./sheet-header.svelte";
  import Title from "./sheet-title.svelte";
  import Description from "./sheet-description.svelte";
  import Footer from "./sheet-footer.svelte";
  import Close from "./sheet-close.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Sheet",
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
          <Button {...props} variant="outline">Abrir sheet</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Header>
          <Title>Filtros</Title>
          <Description>Painel lateral — bom pra filtros ou detalhe sem trocar de tela.</Description>
        </Header>
        <Footer>
          <Close>
            {#snippet child({ props })}
              <Button {...props} variant="outline">Fechar</Button>
            {/snippet}
          </Close>
        </Footer>
      </Content>
    </Root>
  {/snippet}
</Story>
