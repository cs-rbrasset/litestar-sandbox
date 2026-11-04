type Toast = { id: number; text: string; error: boolean };

// $state de módulo: mesmo truque do auth.svelte.ts, sem precisar de contexto/provider
export const toasts = $state<Toast[]>([]);

export function notify(text: string, error = false): void {
  const id = Date.now() + Math.random();
  toasts.push({ id, text, error });
  setTimeout(() => {
    const index = toasts.findIndex((t) => t.id === id);
    if (index !== -1) toasts.splice(index, 1);
  }, error ? 6000 : 3000);
}
