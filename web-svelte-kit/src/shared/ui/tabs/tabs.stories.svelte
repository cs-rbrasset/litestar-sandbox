<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./tabs.svelte";
  import List from "./tabs-list.svelte";
  import Trigger from "./tabs-trigger.svelte";
  import Content from "./tabs-content.svelte";

  const { Story } = defineMeta({
    title: "UI/Tabs",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      disabled: { control: "boolean" },
    },
    args: { disabled: false },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root value="conta" disabled={args.disabled} class="w-72">
      <List>
        <Trigger value="conta">Conta</Trigger>
        <Trigger value="senha">Senha</Trigger>
      </List>
      <Content value="conta">Dados da conta.</Content>
      <Content value="senha">Trocar senha.</Content>
    </Root>
  {/snippet}
</Story>
