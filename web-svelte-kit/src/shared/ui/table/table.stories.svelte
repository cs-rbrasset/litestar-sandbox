<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./table.svelte";
  import Header from "./table-header.svelte";
  import Body from "./table-body.svelte";
  import Row from "./table-row.svelte";
  import Head from "./table-head.svelte";
  import Cell from "./table-cell.svelte";

  const { Story } = defineMeta({
    title: "UI/Table",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<Story name="Playground">
  {#snippet template()}
    <Root class="w-64">
      <Header>
        <Row><Head>Ativo</Head><Head>Qtd.</Head></Row>
      </Header>
      <Body>
        <Row><Cell>CDB123</Cell><Cell>100</Cell></Row>
      </Body>
    </Root>
  {/snippet}
</Story>
