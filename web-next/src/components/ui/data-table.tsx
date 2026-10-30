"use client";

import { tableFeatures, useTable, type ColumnDef, type RowData } from "@tanstack/react-table";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table.tsx";
import { cn } from "../../lib/utils.ts";

// estável em módulo, como o próprio guia da lib recomenda: não invalida os row models a cada render.
// Exportado porque createColumnHelper também precisa dele (mesmo TFeatures em todo lugar).
export const features = tableFeatures({});

// TValue = any: cada coluna infere seu próprio valor (string, number, enum...) e um array
// heterogêneo não tipa em cima de um TValue único sem isso (contravariância no "footer").
export type DataTableColumn<TData extends RowData> = ColumnDef<typeof features, TData, any>;

export function DataTable<TData extends RowData>({
  columns,
  data,
  numericColumnIds = [],
}: {
  columns: DataTableColumn<TData>[];
  data: TData[];
  numericColumnIds?: string[];
}) {
  const table = useTable({ features, columns, data });

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((group) => (
          <TableRow key={group.id}>
            {group.headers.map((header) => (
              <TableHead
                key={header.id}
                className={cn(numericColumnIds.includes(header.column.id) && "text-right")}
              >
                {header.isPlaceholder ? null : <table.FlexRender header={header} />}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getAllCells().map((cell) => (
              <TableCell
                key={cell.id}
                className={cn(
                  numericColumnIds.includes(cell.column.id) && "text-right tabular-nums",
                )}
              >
                <table.FlexRender cell={cell} />
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
