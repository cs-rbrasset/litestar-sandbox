<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./breadcrumb.svelte";
  import List from "./breadcrumb-list.svelte";
  import Item from "./breadcrumb-item.svelte";
  import Link from "./breadcrumb-link.svelte";
  import Separator from "./breadcrumb-separator.svelte";
  import Page from "./breadcrumb-page.svelte";

  const { Story } = defineMeta({
    title: "UI/Breadcrumb",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root>
      <List>
        <Item><Link href="/">Ativos</Link></Item>
        <Separator />
        <Item><Page>CDB123</Page></Item>
      </List>
    </Root>
  {/snippet}
</Story>
