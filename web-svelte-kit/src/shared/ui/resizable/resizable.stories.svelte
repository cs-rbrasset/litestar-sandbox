<script module lang="ts">
  const unsafeArgs = (v: unknown) => v as any;

  import { defineMeta } from "@storybook/addon-svelte-csf";
  import PaneGroup from "./resizable-pane-group.svelte";
  import { Pane } from "paneforge";
  import Handle from "./resizable-handle.svelte";

  const { Story } = defineMeta({
    title: "UI/Resizable",
    component: PaneGroup,
    tags: ["autodocs"],
    argTypes: {
      direction: { control: "select", options: ["horizontal", "vertical"] },
    },
    args: { direction: "horizontal" },
  });
</script>

<Story name="Playground" args={{ direction: "horizontal" }}>
  {#snippet template(args)}
    <PaneGroup {...unsafeArgs(args)} class="h-32 w-80 rounded-md border border-border">
      <Pane defaultSize={50} class="flex items-center justify-center p-4 text-sm">Painel A</Pane>
      <Handle />
      <Pane defaultSize={50} class="flex items-center justify-center p-4 text-sm">Painel B</Pane>
    </PaneGroup>
  {/snippet}
</Story>
