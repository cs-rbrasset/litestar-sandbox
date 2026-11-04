<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./select.svelte";
  import Content from "./select-content.svelte";
  import Item from "./select-item.svelte";
  import Trigger from "./select-trigger.svelte";
  import Value from "./select-value.svelte";

  const { Story } = defineMeta({
    title: "UI/Select",
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
    <Root type="single" value="b" disabled={args.disabled}>
      <Trigger class="w-48">
        <Value placeholder="Selecione" />
      </Trigger>
      <Content>
        <Item value="a" label="Opção A">Opção A</Item>
        <Item value="b" label="Opção B">Opção B</Item>
        <Item value="c" label="Opção C">Opção C</Item>
      </Content>
    </Root>
  {/snippet}
</Story>
