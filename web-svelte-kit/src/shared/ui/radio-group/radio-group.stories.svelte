<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./radio-group.svelte";
  import Item from "./radio-group-item.svelte";
  import { Label } from "#shared/ui/label/index.ts";

  const { Story } = defineMeta({
    title: "UI/RadioGroup",
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
    <Root value="monthly" disabled={args.disabled} class="flex gap-4">
      <div class="flex items-center gap-2">
        <Item value="monthly" id="r1" />
        <Label for="r1">Mensal</Label>
      </div>
      <div class="flex items-center gap-2">
        <Item value="yearly" id="r2" />
        <Label for="r2">Anual</Label>
      </div>
    </Root>
  {/snippet}
</Story>
