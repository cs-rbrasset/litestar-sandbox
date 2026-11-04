<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./tooltip.svelte";
  import Trigger from "./tooltip-trigger.svelte";
  import Content from "./tooltip-content.svelte";
  import Provider from "./tooltip-provider.svelte";
  import { Button } from "#shared/ui/button/index.ts";
  import { Bell } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/Tooltip",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Provider delayDuration={150}>
      <Root>
        <Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline" size="icon"><Bell data-icon="inline-start" /></Button>
          {/snippet}
        </Trigger>
        <Content>Notificações</Content>
      </Root>
    </Provider>
  {/snippet}
</Story>
