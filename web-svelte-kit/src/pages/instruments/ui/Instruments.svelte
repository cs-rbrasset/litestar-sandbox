<script lang="ts">
  import { createColumnHelper, renderSnippet } from "@tanstack/svelte-table";

  import { describeError, useInstruments, type InstrumentType } from "#shared/api/index.ts";
  import { notify } from "#shared/ui/toast/index.ts";
  import {
    Badge,
    Button,
    Card,
    CardAction,
    CardContent,
    CardDescription,
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
  import DataTable, { features } from "#shared/ui/DataTable.svelte";

  import { useArchiveInstrument, useCreateInstrument } from "../api/instruments.ts";

  const TYPES: InstrumentType[] = ["CRI", "DEB", "CDB", "LCI"];

  type Instrument = {
    id: number;
    cetip_code: string;
    name: string;
    instrument_type: InstrumentType;
  };

  const instruments = useInstruments();
  const create = useCreateInstrument();
  const archive = useArchiveInstrument();

  let form = $state({ name: "", cetip_code: "", instrument_type: "CRI" as InstrumentType });

  function submit(event: SubmitEvent) {
    event.preventDefault();
    create.mutate(
      { ...form },
      {
        onSuccess: (created) => {
          notify(`Ativo ${created.cetip_code} cadastrado`);
          form.name = "";
          form.cetip_code = "";
        },
        onError: (error) => notify(describeError(error), true),
      },
    );
  }

  function archiveOne(item: Instrument) {
    archive.mutate(item.id, {
      onSuccess: () => notify(`Ativo ${item.cetip_code} arquivado`),
      onError: (error) => notify(describeError(error), true),
    });
  }

  const items = $derived(instruments.data?.items ?? []);

  const helper = createColumnHelper<typeof features, Instrument>();
  const columns = $derived([
    helper.accessor("cetip_code", {
      header: "Código",
      cell: (ctx) => renderSnippet(cetipCodeCell, ctx.getValue()),
    }),
    helper.accessor("name", { header: "Nome" }),
    helper.accessor("instrument_type", {
      header: "Tipo",
      cell: (ctx) => renderSnippet(instrumentTypeCell, ctx.getValue()),
    }),
    helper.display({
      id: "actions",
      cell: (ctx) => renderSnippet(actionsCell, ctx.row.original),
    }),
  ]);
</script>

{#snippet cetipCodeCell(value: string)}
  <span class="font-mono text-[13px]">{value}</span>
{/snippet}

{#snippet instrumentTypeCell(value: InstrumentType)}
  <Badge class="bg-brand-100 text-brand-700 dark:bg-brand-700/30 dark:text-brand-100">{value}</Badge>
{/snippet}

{#snippet actionsCell(item: Instrument)}
  <div class="text-right">
    <Button variant="destructive" size="sm" disabled={archive.isPending} onclick={() => archiveOne(item)}>
      Arquivar
    </Button>
  </div>
{/snippet}

<div class="grid gap-6 lg:grid-cols-[22rem_1fr]">
  <Card>
    <CardHeader>
      <CardTitle>Novo ativo</CardTitle>
      <CardAction><InfoTooltip text="O código CETIP é normalizado para maiúsculas." /></CardAction>
    </CardHeader>
    <CardContent>
      <form onsubmit={submit} class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <Label for="name">Nome</Label>
          <Input id="name" bind:value={form.name} required />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="cetip_code">Código CETIP</Label>
          <Input id="cetip_code" bind:value={form.cetip_code} class="font-mono text-[13px]" required />
          <span class="text-muted-foreground text-xs">4 a 20 letras ou números</span>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="instrument_type">Tipo</Label>
          <Select type="single" bind:value={form.instrument_type}>
            <SelectTrigger id="instrument_type" class="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {#each TYPES as t (t)}
                <SelectItem value={t}>{t}</SelectItem>
              {/each}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Salvando…" : "Cadastrar ativo"}
        </Button>
      </form>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>Ativos cadastrados</CardTitle>
      <CardDescription>{`${instruments.data?.total ?? 0} em uso; os arquivados não aparecem`}</CardDescription>
    </CardHeader>
    <CardContent>
      {#if instruments.isLoading}
        <Loading label="Carregando ativos" />
      {:else if items.length === 0}
        <p class="text-muted-foreground py-8 text-center text-sm">
          Nenhum ativo ainda. Cadastre o primeiro ao lado.
        </p>
      {:else}
        <DataTable {columns} data={items} />
      {/if}
    </CardContent>
  </Card>
</div>
