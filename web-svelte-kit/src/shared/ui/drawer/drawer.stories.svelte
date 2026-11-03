<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./drawer.svelte";
  import Trigger from "./drawer-trigger.svelte";
  import Content from "./drawer-content.svelte";
  import Header from "./drawer-header.svelte";
  import Title from "./drawer-title.svelte";
  import Description from "./drawer-description.svelte";
  import Footer from "./drawer-footer.svelte";
  import Close from "./drawer-close.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Drawer",
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
          <Button {...props} variant="outline">Abrir drawer</Button>
        {/snippet}
      </Trigger>
      <Content>
        <Header>
          <Title>Ações rápidas</Title>
          <Description>Melhor que Sheet em telas estreitas (mobile).</Description>
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
