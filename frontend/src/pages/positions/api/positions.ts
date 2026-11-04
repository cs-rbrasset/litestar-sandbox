import { createMutation, createQuery } from "@tanstack/svelte-query";

import {
  apiV1PositionsGetPositions,
  apiV1PositionsReportsTaskRunIdGetReport,
  apiV1PositionsReportsTaskRunIdPdfGetReportPdf,
  apiV1PositionsReportsTriggerReport,
  unwrap,
  type PositionsReportRequest,
} from "#shared/api/index.ts";

// o próprio Prefect guarda o estado da execução; aqui é só saber quando parar de perguntar
const REPORT_TERMINAL_STATES = new Set(["COMPLETED", "FAILED", "CRASHED", "CANCELLED"]);

export const keys = {
  positions: (fundCnpj: string, referenceDate: string) => ["positions", fundCnpj, referenceDate] as const,
};

/** fundCnpj/referenceDate vêm como getters: createQuery só reage lendo-os dentro do accessor. */
export function usePositions(fundCnpj: () => string, referenceDate: () => string) {
  return createQuery(() => ({
    queryKey: keys.positions(fundCnpj(), referenceDate()),
    queryFn: () =>
      unwrap(
        apiV1PositionsGetPositions({
          query: { fund_cnpj: fundCnpj(), reference_date: referenceDate() },
        }),
      ),
    enabled: /^\d{14}$/.test(fundCnpj()) && referenceDate() !== "",
  }));
}

/** Sem endpoint de série temporal: busca cada data em paralelo (lista já vem amostrada/limitada). */
export function usePositionsHistory(fundCnpj: () => string, dates: () => string[]) {
  return createQuery(() => ({
    queryKey: ["positions-history", fundCnpj(), dates()] as const,
    queryFn: async () => {
      const byDate = await Promise.all(
        dates().map((reference_date) =>
          unwrap(apiV1PositionsGetPositions({ query: { fund_cnpj: fundCnpj(), reference_date } })),
        ),
      );
      return dates().map((date, i) => ({ date, items: byDate[i] }));
    },
    enabled: /^\d{14}$/.test(fundCnpj()) && dates().length > 0,
  }));
}

export function useTriggerPositionsReport() {
  return createMutation(() => ({
    mutationFn: (body: PositionsReportRequest) =>
      unwrap(apiV1PositionsReportsTriggerReport({ body })),
  }));
}

export function usePositionsReportStatus(taskRunId: () => string | null) {
  return createQuery(() => ({
    queryKey: ["positions-report", taskRunId()],
    queryFn: () =>
      unwrap(apiV1PositionsReportsTaskRunIdGetReport({ path: { task_run_id: taskRunId()! } })),
    enabled: taskRunId() !== null,
    refetchInterval: (query) =>
      REPORT_TERMINAL_STATES.has(query.state.data?.state ?? "") ? false : 1500,
  }));
}

export function useRequestPdfUrl() {
  return createMutation(() => ({
    mutationFn: (taskRunId: string) =>
      unwrap(apiV1PositionsReportsTaskRunIdPdfGetReportPdf({ path: { task_run_id: taskRunId } })),
  }));
}
