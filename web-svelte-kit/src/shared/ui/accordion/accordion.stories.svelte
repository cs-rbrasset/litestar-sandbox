<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./accordion.svelte";
  import Item from "./accordion-item.svelte";
  import Trigger from "./accordion-trigger.svelte";
  import Content from "./accordion-content.svelte";

  const { Story } = defineMeta({
    title: "UI/Accordion",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      disabled: { control: "boolean" },
    },
    args: { disabled: false },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root type="single" value="item-1" disabled={args.disabled} class="w-80">
      <Item value="item-1">
        <Trigger>O que é FSD?</Trigger>
        <Content>Feature-Sliced Design — ver frontend-decisions.md.</Content>
      </Item>
      <Item value="item-2">
        <Trigger>Por que shadcn-svelte?</Trigger>
        <Content>Copy-paste, não dependência — controle total.</Content>
      </Item>
    </Root>
  {/snippet}
</Story>
