<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./popover.svelte";
  import Trigger from "./popover-trigger.svelte";
  import Content from "./popover-content.svelte";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Popover",
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
          <Button {...props} variant="outline">Abrir popover</Button>
        {/snippet}
      </Trigger>
      <Content class="text-sm">Conteúdo flutuante ancorado no trigger.</Content>
    </Root>
  {/snippet}
</Story>
