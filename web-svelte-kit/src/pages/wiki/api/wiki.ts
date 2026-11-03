import { createQuery } from "@tanstack/svelte-query";

import { apiV1NotesWikiListWikiEntries, unwrap } from "#shared/api/index.ts";

export const keys = {
  entries: ["notes", "wiki"] as const,
};

export function useWikiEntries() {
  return createQuery(() => ({
    queryKey: keys.entries,
    queryFn: () => unwrap(apiV1NotesWikiListWikiEntries()),
  }));
}
