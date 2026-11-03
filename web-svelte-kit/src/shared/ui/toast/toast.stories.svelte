<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Toasts from "./Toasts.svelte";
  import { notify } from "./toast.svelte.ts";
  import { Button } from "#shared/ui/button/index.ts";

  const { Story } = defineMeta({
    title: "UI/Toast",
    component: Toasts,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <div class="flex gap-2">
      <Button variant="outline" onclick={() => notify("Boleta #42 registrada")}>Disparar toast</Button>
      <Button variant="outline" onclick={() => notify("Falha ao salvar", true)}>Disparar erro</Button>
    </div>
    <Toasts />
  {/snippet}
</Story>
