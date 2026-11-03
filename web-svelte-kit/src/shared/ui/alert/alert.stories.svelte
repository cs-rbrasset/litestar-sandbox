<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./alert.svelte";
  import Title from "./alert-title.svelte";
  import Description from "./alert-description.svelte";
  import { CircleAlert } from "@lucide/svelte";

  const { Story } = defineMeta({
    title: "UI/Alert",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      variant: { control: "select", options: ["default", "destructive"] },
    },
    args: { variant: "default" },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Root {...args} class="w-80">
      <CircleAlert />
      <Title>Atenção</Title>
      <Description>Mensagem informativa, sem bloquear a tela.</Description>
    </Root>
  {/snippet}
</Story>
