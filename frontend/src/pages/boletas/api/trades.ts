import { createMutation, createQuery, useQueryClient } from "@tanstack/svelte-query";

import {
  apiV1BoletasCreateTrade,
  apiV1BoletasListTrades,
  apiV1BoletasTradeIdCancelCancelTrade,
  apiV1BoletasTradeIdSettleSettleTrade,
  unwrap,
  type TradeCreate,
} from "#shared/api/index.ts";

export const keys = {
  trades: ["trades"] as const,
};

export function useTrades() {
  return createQuery(() => ({
    queryKey: keys.trades,
    queryFn: () => unwrap(apiV1BoletasListTrades({ query: { pageSize: 100 } })),
  }));
}

export function useCreateTrade() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (body: TradeCreate) => unwrap(apiV1BoletasCreateTrade({ body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.trades }),
  }));
}

export function useTransitionTrade() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: ({ id, action }: { id: number; action: "settle" | "cancel" }) => {
      const options = { path: { trade_id: id } };
      return unwrap(
        action === "settle"
          ? apiV1BoletasTradeIdSettleSettleTrade(options)
          : apiV1BoletasTradeIdCancelCancelTrade(options),
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: keys.trades });
      // o TradeSettled é processado em segundo plano: a movimentação chega logo depois da resposta
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["positions"] }), 400);
    },
  }));
}
