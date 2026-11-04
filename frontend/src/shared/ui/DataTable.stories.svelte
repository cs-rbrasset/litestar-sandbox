<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import { createColumnHelper, renderComponent } from "@tanstack/svelte-table";
  import DataTable, { features } from "./DataTable.svelte";
  import DataTableColumnHeader from "./table/data-table-column-header/data-table-column-header.svelte";
  import DataTableView from "./table/data-table-view/data-table-view.svelte";

  const { Story } = defineMeta({
    title: "UI/DataTable",
    component: DataTable,
    tags: ["autodocs"],
  });

  type Row = { id: number; ativo: string; quantidade: number; preco: string };

  const helper = createColumnHelper<typeof features, Row>();
  const columns = [
    helper.accessor("ativo", {
      header: (ctx) => renderComponent(DataTableColumnHeader, { column: ctx.column, title: "Ativo" }),
    }),
    helper.accessor("quantidade", {
      header: (ctx) => renderComponent(DataTableColumnHeader, { column: ctx.column, title: "Qtd." }),
    }),
    helper.accessor("preco", { header: "Preço", enableSorting: false }),
  ];

  const data: Row[] = [
    { id: 1, ativo: "CDB123", quantidade: 100, preco: "101,25" },
    { id: 2, ativo: "LCA456", quantidade: 50, preco: "998,00" },
  ];
</script>

<!-- numericColumnIds alinha cabeçalho e célula à direita. Cabeçalho ordenável usa
  DataTableColumnHeader (sort/esconder no menu); DataTableView no toolbar esconde/mostra
  coluna globalmente — mesmo uso de Trades.svelte. -->
<Story name="Playground">
  {#snippet template()}
    <DataTable
      {columns}
      {data}
      numericColumnIds={["quantidade", "preco"]}
    >
      {#snippet toolbar({ table })}
        <DataTableView {table} label="Colunas" />
      {/snippet}
    </DataTable>
  {/snippet}
</Story>
