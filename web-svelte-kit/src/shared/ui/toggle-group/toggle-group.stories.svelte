<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./toggle-group.svelte";
  import Item from "./toggle-group-item.svelte";

  const { Story } = defineMeta({
    title: "UI/ToggleGroup",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      variant: { control: "select", options: ["default", "outline"] },
      size: { control: "select", options: ["default", "sm", "lg"] },
    },
    args: { variant: "default", size: "default" },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root type="single" value="center" variant={args.variant} size={args.size}>
      <Item value="left" aria-label="Esquerda">E</Item>
      <Item value="center" aria-label="Centro">C</Item>
      <Item value="right" aria-label="Direita">D</Item>
    </Root>
  {/snippet}
</Story>
