<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./card.svelte";
  import Header from "./card-header.svelte";
  import Title from "./card-title.svelte";
  import Description from "./card-description.svelte";
  import Action from "./card-action.svelte";
  import Content from "./card-content.svelte";
  import { InfoTooltip } from "#shared/ui/info-tooltip/index.ts";
  import { TooltipProvider } from "#shared/ui/tooltip/index.ts";

  const { Story } = defineMeta({
    title: "UI/Card",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<!-- Header com título e descrição, como o card "Ativos cadastrados" em Instruments.svelte. -->
<Story name="Playground">
  {#snippet template()}
    <Root class="w-80">
      <Header>
        <Title>Ativos cadastrados</Title>
        <Description>12 em uso; os arquivados não aparecem</Description>
      </Header>
      <Content class="text-sm">CDB123 · LCA456 · DEB789</Content>
    </Root>
  {/snippet}
</Story>

<!-- CardAction no canto do header com InfoTooltip: padrão dos cards de formulário (Trades, Positions). -->
<Story name="Com ação no header">
  {#snippet template()}
    <TooltipProvider delayDuration={150}>
      <Root class="w-80">
        <Header>
          <Title>Posição do fundo</Title>
          <Action><InfoTooltip text="Soma das movimentações liquidadas até a data, sem as posições zeradas." /></Action>
        </Header>
        <Content class="text-sm">Nenhuma posição na data selecionada.</Content>
      </Root>
    </TooltipProvider>
  {/snippet}
</Story>
