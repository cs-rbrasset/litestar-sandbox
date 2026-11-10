<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Switch from "./switch.svelte";
  import { Label } from "#shared/ui/label/index.ts";

  const { Story } = defineMeta({
    title: "UI/Switch",
    component: Switch,
    tags: ["autodocs"],
    argTypes: {
      checked: { control: "boolean", description: "Estado atual. No app é sempre `bind:checked`." },
      disabled: { control: "boolean" },
      size: { control: "select", options: ["sm", "default"] },
    },
    args: { checked: true, disabled: false, size: "default" },
  });
</script>

<!-- Sozinho o switch não tem nome acessível: o aria-label supre isso no playground. -->
<Story name="Playground" args={{ "aria-label": "Publicar na wiki" }} />

<!-- Com rótulo visível, como o toggle de publicação em NotepadEditor.svelte. -->
<Story name="Com rótulo">
  {#snippet template(args)}
    <div class="flex items-center gap-2">
      <Switch id="published" checked={args.checked} disabled={args.disabled} size={args.size} />
      <Label for="published">Publicado na wiki</Label>
    </div>
  {/snippet}
</Story>
