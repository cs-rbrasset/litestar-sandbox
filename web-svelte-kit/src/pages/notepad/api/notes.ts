import { createMutation, createQuery, useQueryClient } from "@tanstack/svelte-query";

import {
  apiV1NotesCreateNote,
  apiV1NotesMineListMyNotes,
  apiV1NotesNoteIdDeleteNote,
  apiV1NotesNoteIdGetNote,
  apiV1NotesNoteIdUpdateNote,
  unwrap,
} from "#shared/api/index.ts";

export const keys = {
  mine: ["notes", "mine"] as const,
  note: (id: number) => ["notes", id] as const,
};

export function useMyNotes() {
  return createQuery(() => ({
    queryKey: keys.mine,
    queryFn: () => unwrap(apiV1NotesMineListMyNotes()),
  }));
}

export function useNote(id: () => number) {
  return createQuery(() => ({
    queryKey: keys.note(id()),
    queryFn: () => unwrap(apiV1NotesNoteIdGetNote({ path: { note_id: id() } })),
  }));
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (title: string) => unwrap(apiV1NotesCreateNote({ body: { title } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.mine }),
  }));
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (id: number) => unwrap(apiV1NotesNoteIdDeleteNote({ path: { note_id: id } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.mine }),
  }));
}

export function useSaveNote(id: () => number) {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (body: { title: string; content: Record<string, unknown>; published: boolean }) =>
      unwrap(apiV1NotesNoteIdUpdateNote({ path: { note_id: id() }, body })),
    onSuccess: (note) => {
      queryClient.setQueryData(keys.note(id()), note);
      queryClient.invalidateQueries({ queryKey: keys.mine });
    },
  }));
}
