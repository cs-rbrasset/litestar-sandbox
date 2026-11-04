import { createMutation, useQueryClient } from "@tanstack/svelte-query";

import {
  apiV1AtivosCreateInstrument,
  apiV1AtivosInstrumentIdDeleteInstrument,
  instrumentKeys as keys,
  unwrap,
  type InstrumentCreate,
} from "#shared/api/index.ts";

export function useCreateInstrument() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (body: InstrumentCreate) => unwrap(apiV1AtivosCreateInstrument({ body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.instruments }),
  }));
}

export function useArchiveInstrument() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (id: number) =>
      unwrap(apiV1AtivosInstrumentIdDeleteInstrument({ path: { instrument_id: id } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.instruments }),
  }));
}
