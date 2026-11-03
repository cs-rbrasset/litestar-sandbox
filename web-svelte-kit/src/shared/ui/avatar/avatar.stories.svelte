<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./avatar.svelte";
  import Image from "./avatar-image.svelte";
  import Fallback from "./avatar-fallback.svelte";

  const { Story } = defineMeta({
    title: "UI/Avatar",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="size-10">
      <Image src="/nao-existe.png" alt="Usuário" />
      <Fallback>CS</Fallback>
    </Root>
  {/snippet}
</Story>
