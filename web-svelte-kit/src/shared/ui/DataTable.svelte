<script lang="ts" module>
  import { tableFeatures } from "@tanstack/svelte-table";

  // estável em módulo, como o próprio guia da lib recomenda: não invalida os row models a cada
  // render. Exportado porque createColumnHelper também precisa dele (mesmo TFeatures sempre).
  export const features = tableFeatures({});
</script>

<script lang="ts" generics="TData extends Record<string, any>">
  import { createTable, FlexRender, type ColumnDef } from "@tanstack/svelte-table";

  import { cn } from "../lib/utils.ts";
  import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table/index.ts";

  // TValue = any: cada coluna infere seu próprio valor (string, number, enum...) e um array
  // heterogêneo não tipa em cima de um TValue único sem isso (contravariância no "footer").
  let {
    columns,
    data,
    numericColumnIds = [],
  }: {
    columns: ColumnDef<typeof features, TData, any>[];
    data: TData[];
    numericColumnIds?: string[];
  } = $props();

  const table = createTable({
    features,
    get columns() {
      return columns;
    },
    get data() {
      return data;
    },
  });
</script>

<Table>
  <TableHeader>
    {#each table.getHeaderGroups() as group (group.id)}
      <TableRow>
        {#each group.headers as header (header.id)}
          <TableHead class={cn(numericColumnIds.includes(header.column.id) && "text-right")}>
            {#if !header.isPlaceholder}
              <FlexRender {header} />
            {/if}
          </TableHead>
        {/each}
      </TableRow>
    {/each}
  </TableHeader>
  <TableBody>
    {#each table.getRowModel().rows as row (row.id)}
      <TableRow>
        {#each row.getAllCells() as cell (cell.id)}
          <TableCell class={cn(numericColumnIds.includes(cell.column.id) && "text-right tabular-nums")}>
            <FlexRender {cell} />
          </TableCell>
        {/each}
      </TableRow>
    {/each}
  </TableBody>
</Table>
