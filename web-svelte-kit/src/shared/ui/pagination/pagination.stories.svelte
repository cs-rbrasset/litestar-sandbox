<script module lang="ts">
  const unsafeArgs = (v: unknown) => v as any;

  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./pagination.svelte";
  import Content from "./pagination-content.svelte";
  import Item from "./pagination-item.svelte";
  import Link from "./pagination-link.svelte";
  import Ellipsis from "./pagination-ellipsis.svelte";
  import Previous from "./pagination-previous.svelte";
  import Next from "./pagination-next.svelte";

  const { Story } = defineMeta({
    title: "UI/Pagination",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      count: { control: "number" },
      perPage: { control: "number" },
    },
    args: { count: 100, perPage: 10 },
  });
</script>

<Story name="Playground" args={{ count: 100, perPage: 10 }}>
  {#snippet template(args)}
    <Root {...unsafeArgs(args)}>
      {#snippet children({ pages, currentPage })}
        <Content>
          <Item><Previous /></Item>
          {#each pages as page (page.key)}
            {#if page.type === "ellipsis"}
              <Item><Ellipsis /></Item>
            {:else}
              <Item>
                <Link {page} isActive={currentPage === page.value}>{page.value}</Link>
              </Item>
            {/if}
          {/each}
          <Item><Next /></Item>
        </Content>
      {/snippet}
    </Root>
  {/snippet}
</Story>
