<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import InfoTooltip from "./info-tooltip.svelte";
  import { TooltipProvider } from "#shared/ui/tooltip/index.ts";

  const { Story } = defineMeta({
    title: "UI/InfoTooltip",
    component: InfoTooltip,
    tags: ["autodocs"],
    argTypes: {
      text: { control: "text", description: "Explicação curta da regra de negócio (máx. ~2 linhas, `max-w-64`)." },
    },
    args: { text: "Soma das movimentações liquidadas até a data, sem as posições zeradas." },
  });
</script>

<!-- Precisa de um TooltipProvider acima, como o Shell fornece no app. -->
<Story name="Playground">
  {#snippet template(args)}
    <TooltipProvider delayDuration={150}>
      <InfoTooltip {...args} />
    </TooltipProvider>
  {/snippet}
</Story>
