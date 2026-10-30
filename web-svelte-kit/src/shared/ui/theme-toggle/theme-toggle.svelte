<script lang="ts">
  import { Moon, Sun } from "@lucide/svelte";
  import { theme } from "#shared/theme/index.ts";
  import { Button } from "#shared/ui/button/index.ts";
  import { Tooltip, TooltipContent, TooltipTrigger } from "#shared/ui/tooltip/index.ts";
</script>

<Tooltip>
  <TooltipTrigger>
    {#snippet child({ props })}
      <Button
        {...props}
        variant="ghost"
        size="icon"
        onclick={theme.toggle}
        aria-label={theme.current === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro"}
      >
        {#if theme.current === "dark"}
          <Sun class="size-4" />
        {:else}
          <Moon class="size-4" />
        {/if}
      </Button>
    {/snippet}
  </TooltipTrigger>
  <TooltipContent>{theme.current === "dark" ? "Tema claro" : "Tema escuro"}</TooltipContent>
</Tooltip>
