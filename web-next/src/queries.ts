import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { unwrap } from "./api.ts";
import {
  apiV1InstrumentsCreateInstrument,
  apiV1InstrumentsInstrumentIdDeleteInstrument,
  apiV1InstrumentsListInstruments,
  apiV1PositionsGetPositions,
  apiV1PositionsReportsTaskRunIdGetReport,
  apiV1PositionsReportsTaskRunIdPdfGetReportPdf,
  apiV1PositionsReportsTriggerReport,
  apiV1TradesCreateTrade,
  apiV1TradesListTrades,
  apiV1TradesTradeIdCancelCancelTrade,
  apiV1TradesTradeIdSettleSettleTrade,
} from "./generated/api/sdk.gen.ts";
import type {
  InstrumentCreate,
  PositionsReportRequest,
  TradeCreate,
} from "./generated/api/types.gen.ts";

// o próprio Prefect guarda o estado da execução; aqui é só saber quando parar de perguntar
const REPORT_TERMINAL_STATES = new Set(["COMPLETED", "FAILED", "CRASHED", "CANCELLED"]);

export const keys = {
  instruments: ["instruments"] as const,
  trades: ["trades"] as const,
  positions: (fundCnpj: string, referenceDate: string) => ["positions", fundCnpj, referenceDate] as const,
};

export function useInstruments() {
  return useQuery({
    queryKey: keys.instruments,
    queryFn: () => unwrap(apiV1InstrumentsListInstruments({ query: { pageSize: 100 } })),
  });
}

export function useCreateInstrument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: InstrumentCreate) => unwrap(apiV1InstrumentsCreateInstrument({ body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.instruments }),
  });
}

export function useArchiveInstrument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      unwrap(apiV1InstrumentsInstrumentIdDeleteInstrument({ path: { instrument_id: id } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.instruments }),
  });
}

export function useTrades() {
  return useQuery({
    queryKey: keys.trades,
    queryFn: () => unwrap(apiV1TradesListTrades({ query: { pageSize: 100 } })),
  });
}

export function useCreateTrade() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: TradeCreate) => unwrap(apiV1TradesCreateTrade({ body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.trades }),
  });
}

export function useTransitionTrade() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "settle" | "cancel" }) => {
      const options = { path: { trade_id: id } };
      return unwrap(
        action === "settle"
          ? apiV1TradesTradeIdSettleSettleTrade(options)
          : apiV1TradesTradeIdCancelCancelTrade(options),
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: keys.trades });
      // o TradeSettled é processado em segundo plano: a movimentação chega logo depois da resposta
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["positions"] }), 400);
    },
  });
}

export function usePositions(fundCnpj: string, referenceDate: string) {
  return useQuery({
    queryKey: keys.positions(fundCnpj, referenceDate),
    queryFn: () =>
      unwrap(apiV1PositionsGetPositions({ query: { fund_cnpj: fundCnpj, reference_date: referenceDate } })),
    enabled: /^\d{14}$/.test(fundCnpj) && referenceDate !== "",
  });
}

export function useTriggerPositionsReport() {
  return useMutation({
    mutationFn: (body: PositionsReportRequest) =>
      unwrap(apiV1PositionsReportsTriggerReport({ body })),
  });
}

export function usePositionsReportStatus(taskRunId: string | null) {
  return useQuery({
    queryKey: ["positions-report", taskRunId],
    queryFn: () =>
      unwrap(apiV1PositionsReportsTaskRunIdGetReport({ path: { task_run_id: taskRunId! } })),
    enabled: taskRunId !== null,
    refetchInterval: (query) =>
      REPORT_TERMINAL_STATES.has(query.state.data?.state ?? "") ? false : 1500,
  });
}

export function useRequestPdfUrl() {
  return useMutation({
    mutationFn: (taskRunId: string) =>
      unwrap(apiV1PositionsReportsTaskRunIdPdfGetReportPdf({ path: { task_run_id: taskRunId } })),
  });
}
