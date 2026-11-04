<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import InfoTooltip from "./info-tooltip.svelte";
  import { TooltipProvider } from "#shared/ui/tooltip/index.ts";

  const { Story } = defineMeta({
    title: "UI/InfoTooltip",
    component: InfoTooltip,
    tags: ["autodocs"],
    argTypes: {
      text: { control: "text" },
    },
    args: { text: "Texto de ajuda sobre uma regra de negócio." },
  });
</script>

<Story name="Playground" args={{ text: "Texto de ajuda sobre uma regra de negócio." }}>
  {#snippet template(args)}
    <TooltipProvider delayDuration={150}>
      <InfoTooltip {...args} />
    </TooltipProvider>
  {/snippet}
</Story>
