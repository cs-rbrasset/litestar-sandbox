<script lang="ts">
  import { LineChart } from "layerchart";
  import { curveMonotoneX } from "d3-shape";

  import { describeError, useInstruments } from "#shared/api/index.ts";
  import { datesBetween, format, today } from "#shared/lib/format.ts";
  import {
    Card,
    CardAction,
    CardContent,
    CardHeader,
    CardTitle,
    InfoTooltip,
    Input,
    Label,
    Loading,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  } from "#shared/ui/index.ts";

  import { usePositionsHistory } from "../api/positions.ts";

  let { defaultFund }: { defaultFund: string } = $props();

  function daysAgo(n: number) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toLocaleDateString("sv-SE");
  }

  // svelte-ignore state_referenced_locally -- de propósito: seed de campos editáveis, não espelho ao vivo da prop
  let fund = $state(defaultFund);
  let from = $state(daysAgo(30));
  let to = $state(today());
  let instrumentId = $state("");

  const instruments = useInstruments();
  const options = $derived(instruments.data?.items ?? []);

  $effect(() => {
    if (instrumentId === "" && options.length > 0) {
      instrumentId = String(options[0].id);
    }
  });

  const selectedCode = $derived(options.find((i) => String(i.id) === instrumentId)?.cetip_code);
  const dates = $derived(datesBetween(from, to));
  const validFund = $derived(/^\d{14}$/.test(fund));

  const history = usePositionsHistory(() => fund, () => dates);

  const chartData = $derived(
    (history.data ?? []).map((point) => ({
      date: new Date(`${point.date}T00:00:00`),
      quantity: point.items.find((item) => item.cetip_code === selectedCode)?.quantity ?? 0,
    })),
  );
</script>

<Card>
  <CardHeader>
    <CardTitle>Posição ao longo do tempo</CardTitle>
    <CardAction>
      <InfoTooltip text="Uma chamada por data no intervalo (amostrado em até 30 pontos): não existe endpoint de série temporal." />
    </CardAction>
  </CardHeader>
  <CardContent>
    <div class="mb-6 grid gap-4 sm:grid-cols-[1fr_10rem_10rem_10rem] sm:items-end">
      <div class="flex flex-col gap-1.5">
        <Label for="history-fund">CNPJ do fundo</Label>
        <Input id="history-fund" bind:value={fund} class="font-mono text-[13px]" inputmode="numeric" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="history-instrument">Ativo</Label>
        <Select type="single" bind:value={instrumentId} disabled={options.length === 0}>
          <SelectTrigger id="history-instrument" class="w-full">
            <SelectValue placeholder="Cadastre um ativo" />
          </SelectTrigger>
          <SelectContent>
            {#each options as i (i.id)}
              <SelectItem value={String(i.id)}>{i.cetip_code}</SelectItem>
            {/each}
          </SelectContent>
        </Select>
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="history-from">De</Label>
        <Input id="history-from" type="date" bind:value={from} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="history-to">Até</Label>
        <Input id="history-to" type="date" bind:value={to} />
      </div>
    </div>

    {#if !validFund || !selectedCode}
      <p class="text-muted-foreground py-8 text-center text-sm">Informe o CNPJ e escolha um ativo.</p>
    {:else if history.isError}
      <p class="rounded-lg bg-rose-50 px-4 py-3 text-sm whitespace-pre-line text-rose-700 dark:bg-rose-950 dark:text-rose-300">
        {describeError(history.error)}
      </p>
    {:else if history.isLoading}
      <Loading label="Carregando série" />
    {:else}
      <div class="h-72">
        <LineChart
          data={chartData}
          x="date"
          y="quantity"
          props={{ spline: { curve: curveMonotoneX, class: "stroke-primary" } }}
          padding={{ left: 48, bottom: 24 }}
        />
      </div>
      <p class="text-muted-foreground mt-2 text-xs">
        Quantidade de {selectedCode} liquidada, {dates.length} pontos entre {format.date(from)} e {format.date(to)}.
      </p>
    {/if}
  </CardContent>
</Card>
