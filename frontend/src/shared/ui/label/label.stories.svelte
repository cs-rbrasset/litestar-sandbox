<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Label from "./label.svelte";
  import { Input } from "#shared/ui/input/index.ts";

  const { Story } = defineMeta({
    title: "UI/Label",
    component: Label,
    tags: ["autodocs"],
    argTypes: {
      for: { control: "text", description: "`id` do controle associado — sempre preenchido no app." },
    },
    args: { for: "fund" },
  });
</script>

<Story name="Playground">CNPJ do fundo</Story>

<!-- Associado a um Input por `for`/`id`, como em Positions.svelte. -->
<Story name="Com campo">
  {#snippet template(args)}
    <div class="flex w-64 flex-col gap-1.5">
      <Label for={args.for}>CNPJ do fundo</Label>
      <Input id={args.for} class="font-mono text-[13px]" inputmode="numeric" />
    </div>
  {/snippet}
</Story>
