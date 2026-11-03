<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./hover-card.svelte";
  import Trigger from "./hover-card-trigger.svelte";
  import Content from "./hover-card-content.svelte";

  const { Story } = defineMeta({
    title: "UI/HoverCard",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      openDelay: { control: "number" },
      closeDelay: { control: "number" },
    },
    args: { openDelay: 700, closeDelay: 300 },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root {...args}>
      <Trigger class="cursor-pointer text-sm font-medium underline underline-offset-4">@claudio</Trigger>
      <Content class="text-sm">Aparece no hover — bom pra preview rápido sem clique.</Content>
    </Root>
  {/snippet}
</Story>
