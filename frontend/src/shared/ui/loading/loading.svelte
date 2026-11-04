<script lang="ts">
  import { LoaderCircle } from "@lucide/svelte";
  import { cn } from "#shared/lib/utils.ts";

  let {
    label,
    size = "md",
    class: className,
  }: { label?: string; size?: "sm" | "md" | "lg"; class?: string } = $props();

  const SIZES = { sm: "size-4", md: "size-5", lg: "size-7" } as const;
</script>

<div class={cn("flex items-center justify-center gap-2 py-8 text-muted-foreground text-sm", className)}>
  <LoaderCircle class={cn("animate-spin", SIZES[size])} />
  {#if label}
    <span>{label}</span>
  {/if}
</div>
