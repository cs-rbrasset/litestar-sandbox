<script lang="ts">
  import { toasts } from "./toast.svelte.ts";
</script>

<div class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
  {#each toasts as t (t.id)}
    <div
      class={`pointer-events-auto rounded-xl px-4 py-3 text-sm whitespace-pre-line shadow-lg ${
        t.error ? "bg-rose-600 text-white" : "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
      }`}
    >
      {t.text}
    </div>
  {/each}
</div>
