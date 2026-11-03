<script lang="ts">
  import { createColumnHelper, renderSnippet } from "@tanstack/svelte-table";
  import { NumberFormatStyle, NumericFormat } from "svelte-number-format";
  import { defaults, superForm } from "sveltekit-superforms";
  import { zod4 } from "sveltekit-superforms/adapters";

  import { describeError, useInstruments, type TradeStatus } from "#shared/api/index.ts";
  import { format, today } from "#shared/lib/format.ts";
  import { notify } from "#shared/ui/toast/index.ts";
  import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
    Badge,
    Button,
    Card,
    CardAction,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    FormControl,
    FormField,
    FormFieldErrors,
    FormLabel,
    InfoTooltip,
    Input,
    Loading,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  } from "#shared/ui/index.ts";
  import DataTable, { features } from "#shared/ui/DataTable.svelte";

  import { useCreateTrade, useTrades, useTransitionTrade } from "../api/trades.ts";
  import { tradeCreateSchema } from "../api/schema.ts";

  let { defaultFund }: { defaultFund: string } = $props();

  const STATUS: Record<TradeStatus, { label: string; className: string }> = {
    PENDING: { label: "Pendente", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" },
    SETTLED: {
      label: "Liquidada",
      className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    },
    CANCELLED: { label: "Cancelada", className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300" },
  };

  const instruments = useInstruments();
  const trades = useTrades();
  const create = useCreateTrade();
  const transition = useTransitionTrade();

  const createForm = superForm(
    // svelte-ignore state_referenced_locally -- de propósito: seed do form, não espelho ao vivo da prop
    defaults(
      { fund_cnpj: defaultFund, trade_date: today(), side: "BUY" as const, quantity: 100, unit_price: "100.00" },
      zod4(tradeCreateSchema),
    ),
    {
      SPA: true,
      validators: zod4(tradeCreateSchema),
      resetForm: false,
      onUpdate({ form: validated }) {
        if (!validated.valid) return;
        create.mutate(validated.data, {
          onSuccess: (trade) => notify(`Boleta #${trade.id} registrada`),
          onError: (error) => notify(describeError(error), true),
        });
      },
    },
  );
  const { form: formData, enhance: enhanceForm } = createForm;

  // "0" é o default numérico do schema pro campo ainda não escolhido; vira "" pro placeholder do Select aparecer.
  function instrumentIdValue() {
    return $formData.instrument_id ? String($formData.instrument_id) : "";
  }
  function setInstrumentIdValue(value: string) {
    $formData.instrument_id = value ? Number(value) : 0;
  }

  const options = $derived(instruments.data?.items ?? []);

  // pré-seleciona o primeiro ativo assim que a lista chega, igual o fallback da versão React
  $effect(() => {
    if (!$formData.instrument_id && options.length > 0) {
      $formData.instrument_id = options[0].id;
    }
  });

  function act(id: number, action: "settle" | "cancel") {
    transition.mutate(
      { id, action },
      {
        onSuccess: () => notify(action === "settle" ? `Boleta #${id} liquidada` : `Boleta #${id} cancelada`),
        onError: (error) => notify(describeError(error), true),
      },
    );
  }

  const items = $derived(trades.data?.items ?? []);
  type Trade = (typeof items)[number];

  const helper = createColumnHelper<typeof features, Trade>();
  const columns = $derived([
    helper.accessor("id", { header: "#", cell: (ctx) => renderSnippet(idCell, ctx.getValue()) }),
    helper.accessor("trade_date", { header: "Data", cell: (ctx) => renderSnippet(dateCell, ctx.getValue()) }),
    helper.accessor("cetip_code", { header: "Ativo", cell: (ctx) => renderSnippet(cetipCodeCell, ctx.getValue()) }),
    helper.accessor("side", { header: "Lado", cell: (ctx) => (ctx.getValue() === "BUY" ? "Compra" : "Venda") }),
    helper.accessor("quantity", { header: "Qtd.", cell: (ctx) => renderSnippet(quantityCell, ctx.getValue()) }),
    helper.accessor("unit_price", { header: "Preço", cell: (ctx) => renderSnippet(priceCell, ctx.getValue()) }),
    helper.accessor("status", { header: "Status", cell: (ctx) => renderSnippet(statusCell, ctx.getValue() ?? "PENDING") }),
    helper.display({ id: "actions", cell: (ctx) => renderSnippet(actionsCell, ctx.row.original) }),
  ]);
</script>

{#snippet idCell(value: number)}
  <span class="text-muted-foreground">{value}</span>
{/snippet}

{#snippet dateCell(value: string)}
  <span class="whitespace-nowrap">{format.date(value)}</span>
{/snippet}

{#snippet cetipCodeCell(value: string)}
  <span class="font-mono text-[13px]">{value}</span>
{/snippet}

{#snippet quantityCell(value: number)}
  <span class="tabular-nums">{format.quantity(value)}</span>
{/snippet}

{#snippet priceCell(value: string)}
  <span class="tabular-nums">{format.price(value)}</span>
{/snippet}

{#snippet statusCell(value: TradeStatus)}
  {@const status = STATUS[value]}
  <Badge class={status.className}>{status.label}</Badge>
{/snippet}

{#snippet actionsCell(trade: Trade)}
  {#if trade.status === "PENDING"}
    <div class="flex justify-end gap-1 whitespace-nowrap">
      <Button size="sm" disabled={transition.isPending} onclick={() => act(trade.id, "settle")}>Liquidar</Button>
      <AlertDialog>
        <AlertDialogTrigger>
          {#snippet child({ props })}
            <Button {...props} size="sm" variant="ghost" disabled={transition.isPending}>Cancelar</Button>
          {/snippet}
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar boleta #{trade.id}?</AlertDialogTitle>
            <AlertDialogDescription>Essa ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onclick={() => act(trade.id, "cancel")}>
              Cancelar boleta
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  {/if}
{/snippet}

<div class="grid gap-6 lg:grid-cols-[22rem_1fr]">
  <Card>
    <CardHeader>
      <CardTitle>Nova boleta</CardTitle>
      <CardAction><InfoTooltip text="O ativo é validado pelo instruments.public." /></CardAction>
    </CardHeader>
    <CardContent>
      <form use:enhanceForm class="flex flex-col gap-4">
        <FormField form={createForm} name="instrument_id">
          <FormControl>
            {#snippet children({ props })}
              <FormLabel>Ativo</FormLabel>
              <Select
                type="single"
                bind:value={instrumentIdValue, setInstrumentIdValue}
                disabled={options.length === 0}
                items={options.map((i) => ({ value: String(i.id), label: i.cetip_code }))}
              >
                <SelectTrigger {...props} class="w-full">
                  <SelectValue placeholder="Cadastre um ativo primeiro" />
                </SelectTrigger>
                <SelectContent>
                  {#each options as i (i.id)}
                    <SelectItem value={String(i.id)} label={i.cetip_code}>{i.cetip_code} · {i.name}</SelectItem>
                  {/each}
                </SelectContent>
              </Select>
            {/snippet}
          </FormControl>
          <FormFieldErrors />
        </FormField>

        <FormField form={createForm} name="fund_cnpj">
          <FormControl>
            {#snippet children({ props })}
              <FormLabel>CNPJ do fundo</FormLabel>
              <Input {...props} bind:value={$formData.fund_cnpj} class="font-mono text-[13px]" inputmode="numeric" />
            {/snippet}
          </FormControl>
          <FormFieldErrors />
          <span class="text-muted-foreground text-xs">14 dígitos, sem pontuação</span>
        </FormField>

        <div class="grid grid-cols-2 gap-3">
          <FormField form={createForm} name="trade_date">
            <FormControl>
              {#snippet children({ props })}
                <FormLabel>Data</FormLabel>
                <Input {...props} type="date" bind:value={$formData.trade_date} />
              {/snippet}
            </FormControl>
            <FormFieldErrors />
          </FormField>

          <FormField form={createForm} name="side">
            <FormControl>
              {#snippet children({ props })}
                <FormLabel>Lado</FormLabel>
                <Select type="single" bind:value={$formData.side}>
                  <SelectTrigger {...props} class="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BUY">Compra</SelectItem>
                    <SelectItem value="SELL">Venda</SelectItem>
                  </SelectContent>
                </Select>
              {/snippet}
            </FormControl>
            <FormFieldErrors />
          </FormField>

          <FormField form={createForm} name="quantity">
            <FormControl>
              {#snippet children({ props })}
                <FormLabel>Quantidade</FormLabel>
                <Input {...props} type="number" min={1} bind:value={$formData.quantity} />
              {/snippet}
            </FormControl>
            <FormFieldErrors />
          </FormField>

          <FormField form={createForm} name="unit_price">
            <FormControl>
              {#snippet children({ props })}
                <FormLabel>Preço unitário</FormLabel>
                <NumericFormat
                  {...props}
                  bind:value={$formData.unit_price}
                  valueType="string"
                  locale="pt-BR"
                  options={{ formatStyle: NumberFormatStyle.Decimal, precision: { min: 2, max: 8 } }}
                  class="dark:bg-input/30 border-input focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 h-8 w-full min-w-0 rounded-lg border bg-transparent px-2.5 py-1 text-base outline-none transition-colors focus-visible:ring-3 aria-invalid:ring-3 md:text-sm"
                />
              {/snippet}
            </FormControl>
            <FormFieldErrors />
          </FormField>
        </div>

        <Button type="submit" disabled={create.isPending || options.length === 0}>
          {create.isPending ? "Registrando…" : "Registrar boleta"}
        </Button>
      </form>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>Boletas</CardTitle>
      <CardAction><InfoTooltip text="Liquidar emite o TradeSettled, que o positions escuta." /></CardAction>
    </CardHeader>
    <CardContent>
      {#if trades.isLoading}
        <Loading label="Carregando boletas" />
      {:else if items.length === 0}
        <p class="text-muted-foreground py-8 text-center text-sm">Nenhuma boleta ainda.</p>
      {:else}
        <DataTable {columns} data={items} numericColumnIds={["quantity", "unit_price"]} />
      {/if}
    </CardContent>
  </Card>
</div>
