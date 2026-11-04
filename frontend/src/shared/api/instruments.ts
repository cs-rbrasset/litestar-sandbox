import { createQuery } from "@tanstack/svelte-query";

import { unwrap } from "./litestar-error.ts";
import { apiV1InstrumentsListInstruments } from "./generated/sdk.gen.ts";

// usado por pages/instruments (cadastro) e pages/trades (seleção de ativo na boleta):
// listagem simples, sem regra de negócio, então fica em shared/api, não numa entidade.
export const keys = {
  instruments: ["instruments"] as const,
};

export function useInstruments() {
  return createQuery(() => ({
    queryKey: keys.instruments,
    queryFn: () => unwrap(apiV1InstrumentsListInstruments({ query: { pageSize: 100 } })),
  }));
}
