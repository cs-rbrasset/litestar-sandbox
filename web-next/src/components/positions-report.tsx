"use client";

import { useState } from "react";

import { describeError, today } from "../api.ts";
import { useRequestPdfUrl, usePositionsReportStatus, useTriggerPositionsReport } from "../queries.ts";
import { useNotify } from "./toast.tsx";
import { Badge } from "./ui/badge.tsx";
import { Button } from "./ui/button.tsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card.tsx";
import { Input } from "./ui/input.tsx";
import { Label } from "./ui/label.tsx";

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

export function PositionsReportPanel({ defaultFund }: { defaultFund: string }) {
  const notify = useNotify();
  const [fund, setFund] = useState(defaultFund);
  const [datesInput, setDatesInput] = useState(today());
  const [taskRunId, setTaskRunId] = useState<string | null>(null);
  const trigger = useTriggerPositionsReport();
  const status = usePositionsReportStatus(taskRunId);
  const requestPdfUrl = useRequestPdfUrl();

  const submit = () => {
    const reference_dates = datesInput
      .split(",")
      .map((d) => d.trim())
      .filter(Boolean);
    trigger.mutate(
      { fund_cnpj: fund, reference_dates },
      {
        onSuccess: (handle) => {
          setTaskRunId(handle.task_run_id);
          notify(`Relatório agendado no Prefect (${handle.task_run_id.slice(0, 8)}…)`);
        },
        onError: (error) => notify(describeError(error), true),
      },
    );
  };

  const download = () => {
    if (taskRunId === null) return;
    // signed URL do Supabase Storage: já vem com o próprio token, abre direto, sem nosso Bearer
    requestPdfUrl.mutate(taskRunId, {
      onSuccess: (handle) => window.open(handle.url, "_blank"),
      onError: (error) => notify(describeError(error), true),
    });
  };

  const state = status.data?.state;
  const stateClassName = state ? (STATE_CLASSES[state] ?? STATE_CLASSES.SCHEDULED) : STATE_CLASSES.SCHEDULED;
  const isCompleted = state === "COMPLETED";
  const isFailed = state !== undefined && FAILED_STATES.has(state);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Relatório de posições (Prefect)</CardTitle>
        <CardDescription>Agenda num worker à parte; o PDF sai do Supabase Storage via signed URL.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-6 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="report-fund">CNPJ do fundo</Label>
            <Input
              id="report-fund"
              value={fund}
              onChange={(e) => setFund(e.target.value)}
              className="font-mono text-[13px]"
              inputMode="numeric"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="report-dates">Datas de referência</Label>
            <Input
              id="report-dates"
              value={datesInput}
              onChange={(e) => setDatesInput(e.target.value)}
              className="font-mono text-[13px]"
            />
            <span className="text-xs text-muted-foreground">separadas por vírgula, AAAA-MM-DD</span>
          </div>
          <Button onClick={submit} disabled={trigger.isPending}>
            {trigger.isPending ? "Gerando…" : "Gerar relatório"}
          </Button>
        </div>

        {taskRunId === null ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Nenhum relatório gerado ainda.</p>
        ) : (
          <div className="flex items-center gap-3 text-sm">
            <span className="font-mono text-[13px]">{taskRunId.slice(0, 8)}…</span>
            <Badge className={stateClassName}>{state ?? "consultando…"}</Badge>
            {isCompleted && (
              <Button size="sm" variant="secondary" disabled={requestPdfUrl.isPending} onClick={download}>
                {requestPdfUrl.isPending ? "Buscando…" : "Baixar PDF"}
              </Button>
            )}
            {isFailed && <span className="text-rose-600">o relatório falhou</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
