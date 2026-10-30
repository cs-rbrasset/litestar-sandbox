<script lang="ts">
  import { describeError } from "#shared/api/index.ts";
  import { today } from "#shared/lib/format.ts";
  import { notify } from "#shared/ui/toast/index.ts";
  import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label } from "#shared/ui/index.ts";

  import { useRequestPdfUrl, usePositionsReportStatus, useTriggerPositionsReport } from "../api/positions.ts";

  let { defaultFund }: { defaultFund: string } = $props();

  const STATE_CLASSES: Record<string, string> = {
    SCHEDULED: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    PENDING: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    RUNNING: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
    COMPLETED: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    FAILED: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
    CRASHED: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
    CANCELLED: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    CANCELLING: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    PAUSED: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  };

  const FAILED_STATES = new Set(["FAILED", "CRASHED", "CANCELLED"]);

  // svelte-ignore state_referenced_locally -- de propósito: seed de um campo editável, não espelho ao vivo da prop
  let fund = $state(defaultFund);
  let datesInput = $state(today());
  let taskRunId = $state<string | null>(null);

  const trigger = useTriggerPositionsReport();
  const status = usePositionsReportStatus(() => taskRunId);
  const requestPdfUrl = useRequestPdfUrl();

  function submit() {
    const reference_dates = datesInput
      .split(",")
      .map((d) => d.trim())
      .filter(Boolean);
    trigger.mutate(
      { fund_cnpj: fund, reference_dates },
      {
        onSuccess: (handle) => {
          taskRunId = handle.task_run_id;
          notify(`Relatório agendado no Prefect (${handle.task_run_id.slice(0, 8)}…)`);
        },
        onError: (error) => notify(describeError(error), true),
      },
    );
  }

  function download() {
    if (taskRunId === null) return;
    // signed URL do Supabase Storage: já vem com o próprio token, abre direto, sem nosso Bearer
    requestPdfUrl.mutate(taskRunId, {
      onSuccess: (handle) => window.open(handle.url, "_blank"),
      onError: (error) => notify(describeError(error), true),
    });
  }

  // nome "state" colide com a rune $state (Svelte reinterpreta "$state(...)" como
  // auto-subscribe de uma store chamada "state" quando existe esse binding no escopo)
  const reportState = $derived(status.data?.state);
  const stateClassName = $derived(reportState ? (STATE_CLASSES[reportState] ?? STATE_CLASSES.SCHEDULED) : STATE_CLASSES.SCHEDULED);
  const isCompleted = $derived(reportState === "COMPLETED");
  const isFailed = $derived(reportState !== undefined && FAILED_STATES.has(reportState));
</script>

<Card>
  <CardHeader>
    <CardTitle>Relatório de posições (Prefect)</CardTitle>
    <CardDescription>Agenda num worker à parte; o PDF sai do Supabase Storage via signed URL.</CardDescription>
  </CardHeader>
  <CardContent>
    <div class="mb-6 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
      <div class="flex flex-col gap-1.5">
        <Label for="report-fund">CNPJ do fundo</Label>
        <Input id="report-fund" bind:value={fund} class="font-mono text-[13px]" inputmode="numeric" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="report-dates">Datas de referência</Label>
        <Input id="report-dates" bind:value={datesInput} class="font-mono text-[13px]" />
        <span class="text-muted-foreground text-xs">separadas por vírgula, AAAA-MM-DD</span>
      </div>
      <Button onclick={submit} disabled={trigger.isPending}>
        {trigger.isPending ? "Gerando…" : "Gerar relatório"}
      </Button>
    </div>

    {#if taskRunId === null}
      <p class="text-muted-foreground py-8 text-center text-sm">Nenhum relatório gerado ainda.</p>
    {:else}
      <div class="flex items-center gap-3 text-sm">
        <span class="font-mono text-[13px]">{taskRunId.slice(0, 8)}…</span>
        <Badge class={stateClassName}>{reportState ?? "consultando…"}</Badge>
        {#if isCompleted}
          <Button size="sm" variant="secondary" disabled={requestPdfUrl.isPending} onclick={download}>
            {requestPdfUrl.isPending ? "Buscando…" : "Baixar PDF"}
          </Button>
        {/if}
        {#if isFailed}
          <span class="text-rose-600">o relatório falhou</span>
        {/if}
      </div>
    {/if}
  </CardContent>
</Card>
