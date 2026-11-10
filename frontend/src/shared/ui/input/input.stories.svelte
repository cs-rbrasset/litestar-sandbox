<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Input from "./input.svelte";
  import { Label } from "#shared/ui/label/index.ts";

  const { Story } = defineMeta({
    title: "UI/Input",
    component: Input,
    tags: ["autodocs"],
    argTypes: {
      type: {
        control: "select",
        options: ["text", "number", "date"],
        description: "Os três tipos usados nos formulários do app (nome/CNPJ, quantidade, data).",
      },
      placeholder: { control: "text" },
      disabled: { control: "boolean" },
      required: { control: "boolean" },
    },
    args: { type: "text", placeholder: "Nome do ativo", disabled: false, required: false },
  });
</script>

<!-- Sozinho não tem nome acessível: o aria-label supre isso no playground. -->
<Story name="Playground" args={{ "aria-label": "Nome do ativo" }} />

<!-- Os campos do formulário de boleta (Trades.svelte), cada um com seu Label. -->
<Story name="Campos de boleta">
  {#snippet template()}
    <div class="flex w-72 flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <Label for="fund_cnpj">CNPJ do fundo</Label>
        <Input id="fund_cnpj" value="12345678000190" class="font-mono text-[13px]" inputmode="numeric" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="trade_date">Data da boleta</Label>
        <Input id="trade_date" type="date" value="2026-11-10" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="quantity">Quantidade</Label>
        <Input id="quantity" type="number" min={1} value={100} />
      </div>
    </div>
  {/snippet}
</Story>
