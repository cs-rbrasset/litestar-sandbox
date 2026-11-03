<script module lang="ts">
  const unsafeArgs = (v: unknown) => v as any;

  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./input-otp.svelte";
  import Group from "./input-otp-group.svelte";
  import Slot from "./input-otp-slot.svelte";

  const { Story } = defineMeta({
    title: "UI/InputOTP",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      maxlength: { control: "number" },
    },
    args: { maxlength: 6 },
  });
</script>

<Story name="Playground" args={{ maxlength: 6 }}>
  {#snippet template(args)}
    <Root {...unsafeArgs(args)}>
      {#snippet children({ cells })}
        <Group>
          {#each cells as cell (cell)}
            <Slot {cell} />
          {/each}
        </Group>
      {/snippet}
    </Root>
  {/snippet}
</Story>
