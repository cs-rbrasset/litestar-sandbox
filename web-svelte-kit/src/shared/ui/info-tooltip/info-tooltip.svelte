<script lang="ts">
  import { Info } from "@lucide/svelte";
  import { Tooltip, TooltipContent, TooltipTrigger } from "#shared/ui/tooltip/index.ts";

  let { text }: { text: string } = $props();
</script>

<Tooltip>
  <TooltipTrigger>
    {#snippet child({ props })}
      <button {...props} type="button" class="text-muted-foreground hover:text-foreground">
        <Info class="size-4" />
        <span class="sr-only">Mais informações</span>
      </button>
    {/snippet}
  </TooltipTrigger>
  <TooltipContent class="max-w-64">{text}</TooltipContent>
</Tooltip>
