"use client";

import { useState } from "react";

import { createColumnHelper } from "@tanstack/react-table";

import { describeError, format, today } from "../api.ts";
import { usePositions } from "../queries.ts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card.tsx";
import { DataTable, features } from "./ui/data-table.tsx";
import { Input } from "./ui/input.tsx";
import { Label } from "./ui/label.tsx";

export function PositionsPanel({ defaultFund }: { defaultFund: string }) {
  const [fund, setFund] = useState(defaultFund);
  const [date, setDate] = useState(today());
  const positions = usePositions(fund, date);
  const items = positions.data ?? [];
  const validFund = /^\d{14}$/.test(fund);

  type Position = (typeof items)[number];
  const helper = createColumnHelper<typeof features, Position>();
  const columns = [
    helper.accessor("cetip_code", { header: "Ativo", cell: (ctx) => <span className="font-mono text-[13px]">{ctx.getValue()}</span> }),
    helper.accessor("quantity", {
      header: "Quantidade",
      cell: (ctx) => (
        <span className={`font-medium tabular-nums ${ctx.getValue() < 0 ? "text-rose-600" : ""}`}>
          {format.quantity(ctx.getValue())}
        </span>
      ),
    }),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Posição do fundo</CardTitle>
        <CardDescription>Soma das movimentações liquidadas até a data, sem as posições zeradas.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-6 grid gap-4 sm:grid-cols-[1fr_12rem]">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="fund">CNPJ do fundo</Label>
            <Input
              id="fund"
              value={fund}
              onChange={(e) => setFund(e.target.value)}
              className="font-mono text-[13px]"
              inputMode="numeric"
            />
            <span className="text-xs text-muted-foreground">
              {validFund ? format.cnpj(fund) : "14 dígitos, sem pontuação"}
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="date">Data de referência</Label>
            <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </div>

        {!validFund ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Informe um CNPJ com 14 dígitos.</p>
        ) : positions.isError ? (
          <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm whitespace-pre-line text-rose-700 dark:bg-rose-950 dark:text-rose-300">
            {describeError(positions.error)}
          </p>
        ) : positions.isLoading ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Carregando…</p>
        ) : items.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Sem posição em {format.date(date)}.</p>
        ) : (
          <DataTable columns={columns} data={items} numericColumnIds={["quantity"]} />
        )}
      </CardContent>
    </Card>
  );
}
