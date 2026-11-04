<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import ThemeToggle from "./theme-toggle.svelte";
  import { TooltipProvider } from "#shared/ui/tooltip/index.ts";

  const { Story } = defineMeta({
    title: "UI/ThemeToggle",
    component: ThemeToggle,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <TooltipProvider delayDuration={150}>
      <ThemeToggle />
    </TooltipProvider>
  {/snippet}
</Story>
