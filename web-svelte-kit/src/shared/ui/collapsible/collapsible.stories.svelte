<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./collapsible.svelte";
  import Trigger from "./collapsible-trigger.svelte";
  import Content from "./collapsible-content.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Collapsible",
    component: Root,
    tags: ["autodocs"],
    argTypes: { open: { control: "boolean" } },
    args: { open: false },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root {...args} class="w-64">
      <Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="outline" size="sm">Mostrar detalhes</Button>
        {/snippet}
      </Trigger>
      <Content class="pt-2 text-sm text-muted-foreground">Conteúdo extra, sem o chrome de item de Accordion.</Content>
    </Root>
  {/snippet}
</Story>
