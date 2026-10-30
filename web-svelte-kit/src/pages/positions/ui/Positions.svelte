<script lang="ts">
  import { createColumnHelper, renderSnippet } from "@tanstack/svelte-table";

  import { describeError } from "#shared/api/index.ts";
  import { format, today } from "#shared/lib/format.ts";
  import { Card, CardAction, CardContent, CardHeader, CardTitle, InfoTooltip, Input, Label, Loading } from "#shared/ui/index.ts";
  import DataTable, { features } from "#shared/ui/DataTable.svelte";

  import { usePositions } from "../api/positions.ts";

  let { defaultFund }: { defaultFund: string } = $props();

  // svelte-ignore state_referenced_locally -- de propósito: seed de um campo editável, não espelho ao vivo da prop
  let fund = $state(defaultFund);
  let date = $state(today());

  const positions = usePositions(() => fund, () => date);

  const items = $derived(positions.data ?? []);
  const validFund = $derived(/^\d{14}$/.test(fund));

  type Position = (typeof items)[number];
  const helper = createColumnHelper<typeof features, Position>();
  const columns = $derived([
    helper.accessor("cetip_code", { header: "Ativo", cell: (ctx) => renderSnippet(cetipCodeCell, ctx.getValue()) }),
    helper.accessor("quantity", { header: "Quantidade", cell: (ctx) => renderSnippet(quantityCell, ctx.getValue()) }),
  ]);
</script>

{#snippet cetipCodeCell(value: string)}
  <span class="font-mono text-[13px]">{value}</span>
{/snippet}

{#snippet quantityCell(value: number)}
  <span class={`font-medium tabular-nums ${value < 0 ? "text-rose-600" : ""}`}>{format.quantity(value)}</span>
{/snippet}

<Card>
  <CardHeader>
    <CardTitle>Posição do fundo</CardTitle>
    <CardAction>
      <InfoTooltip text="Soma das movimentações liquidadas até a data, sem as posições zeradas." />
    </CardAction>
  </CardHeader>
  <CardContent>
    <div class="mb-6 grid gap-4 sm:grid-cols-[1fr_12rem]">
      <div class="flex flex-col gap-1.5">
        <Label for="fund">CNPJ do fundo</Label>
        <Input id="fund" bind:value={fund} class="font-mono text-[13px]" inputmode="numeric" />
        <span class="text-muted-foreground text-xs">{validFund ? format.cnpj(fund) : "14 dígitos, sem pontuação"}</span>
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="date">Data de referência</Label>
        <Input id="date" type="date" bind:value={date} />
      </div>
    </div>

    {#if !validFund}
      <p class="text-muted-foreground py-8 text-center text-sm">Informe um CNPJ com 14 dígitos.</p>
    {:else if positions.isError}
      <p class="rounded-lg bg-rose-50 px-4 py-3 text-sm whitespace-pre-line text-rose-700 dark:bg-rose-950 dark:text-rose-300">
        {describeError(positions.error)}
      </p>
    {:else if positions.isLoading}
      <Loading label="Carregando posição" />
    {:else if items.length === 0}
      <p class="text-muted-foreground py-8 text-center text-sm">Sem posição em {format.date(date)}.</p>
    {:else}
      <DataTable {columns} data={items} numericColumnIds={["quantity"]} />
    {/if}
  </CardContent>
</Card>
