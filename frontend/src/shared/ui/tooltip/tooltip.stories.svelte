<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./tooltip.svelte";
  import Trigger from "./tooltip-trigger.svelte";
  import Content from "./tooltip-content.svelte";
  import Provider from "./tooltip-provider.svelte";
  import { Button } from "#shared/ui/button/index.ts";
  import { ExternalLink } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/Tooltip",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<!-- Botão só com ícone: o tooltip explica, o aria-label nomeia para leitor de tela. -->
<Story name="Playground">
  {#snippet template()}
    <Provider delayDuration={150}>
      <Root>
        <Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline" size="icon" aria-label="Documentação da API">
              <ExternalLink />
            </Button>
          {/snippet}
        </Trigger>
        <Content>Documentação da API</Content>
      </Root>
    </Provider>
  {/snippet}
</Story>

<!-- `TooltipContent side="right"`: como os itens da Sidebar recolhida. -->
<Story name="À direita">
  {#snippet template()}
    <Provider delayDuration={150}>
      <Root>
        <Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="icon" aria-label="Boletas">
              <ExternalLink />
            </Button>
          {/snippet}
        </Trigger>
        <Content side="right">Boletas</Content>
      </Root>
    </Provider>
  {/snippet}
</Story>
