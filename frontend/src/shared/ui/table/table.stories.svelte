<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./table.svelte";
  import Header from "./table-header.svelte";
  import Body from "./table-body.svelte";
  import Row from "./table-row.svelte";
  import Head from "./table-head.svelte";
  import Cell from "./table-cell.svelte";

  const TRADES = [
    { id: 41, ativo: "CDB123", lado: "Compra", quantidade: "100", preco: "101,25" },
    { id: 42, ativo: "LCA456", lado: "Venda", quantidade: "50", preco: "998,00" },
    { id: 43, ativo: "DEB789", lado: "Compra", quantidade: "1.000", preco: "1.012,40" },
  ];

  const { Story } = defineMeta({
    title: "UI/Table",
    component: Root,
    tags: ["autodocs"],
  });
</script>

<!-- Primitivas de tabela puras. Colunas numéricas à direita com tabular-nums, como o DataTable faz. -->
<Story name="Playground">
  {#snippet template()}
    <Root class="w-96">
      <Header>
        <Row>
          <Head>#</Head>
          <Head>Ativo</Head>
          <Head>Lado</Head>
          <Head class="text-right">Qtd.</Head>
          <Head class="text-right">Preço</Head>
        </Row>
      </Header>
      <Body>
        {#each TRADES as trade (trade.id)}
          <Row>
            <Cell class="text-muted-foreground">{trade.id}</Cell>
            <Cell class="font-mono text-[13px]">{trade.ativo}</Cell>
            <Cell>{trade.lado}</Cell>
            <Cell class="text-right tabular-nums">{trade.quantidade}</Cell>
            <Cell class="text-right tabular-nums">{trade.preco}</Cell>
          </Row>
        {/each}
      </Body>
    </Root>
  {/snippet}
</Story>
