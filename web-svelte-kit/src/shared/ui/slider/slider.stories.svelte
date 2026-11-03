<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Slider from "./slider.svelte";

  const { Story } = defineMeta({
    title: "UI/Slider",
    component: Slider,
    tags: ["autodocs"],
    argTypes: {
      value: { control: "number" },
      min: { control: "number" },
      max: { control: "number" },
      step: { control: "number" },
      disabled: { control: "boolean" },
    },
    args: { value: 40, min: 0, max: 100, step: 1, disabled: false },
  });
</script>

<Story name="Playground">
  {#snippet template(args)}
    <Slider
      type="single"
      value={args.value as number}
      min={args.min}
      max={args.max}
      step={args.step}
      disabled={args.disabled}
      class="w-64"
    />
  {/snippet}
</Story>
