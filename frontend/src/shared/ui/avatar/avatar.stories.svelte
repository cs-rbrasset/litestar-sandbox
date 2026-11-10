<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./avatar.svelte";
  import Image from "./avatar-image.svelte";
  import Fallback from "./avatar-fallback.svelte";

  const SIZES = ["sm", "default", "lg"] as const;

  const { Story } = defineMeta({
    title: "UI/Avatar",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      size: {
        control: "select",
        options: SIZES,
        description: "`sm` no menu do cabeçalho (Shell), `lg` no card de perfil (Home).",
      },
    },
    args: { size: "default" },
  });
</script>

<!-- A imagem não carrega de propósito: no app não há foto, só as iniciais da conta. -->
<Story name="Playground">
  {#snippet template(args)}
    <Root size={args.size}>
      <Image src="/nao-existe.png" alt="Foto de Claudio Silva" />
      <Fallback>CS</Fallback>
    </Root>
  {/snippet}
</Story>

<Story name="Tamanhos">
  {#snippet template()}
    <div class="flex items-center gap-3">
      {#each SIZES as size (size)}
        <Root {size}>
          <Fallback>CS</Fallback>
        </Root>
      {/each}
    </div>
  {/snippet}
</Story>
