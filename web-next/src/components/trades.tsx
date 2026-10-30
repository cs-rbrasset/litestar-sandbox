"use client";

import { useState, type FormEvent } from "react";

import { createColumnHelper } from "@tanstack/react-table";

import { describeError, format, today } from "../api.ts";
import type { TradeSide, TradeStatus } from "../generated/api/types.gen.ts";
import { useCreateTrade, useInstruments, useTrades, useTransitionTrade } from "../queries.ts";
import { useNotify } from "./toast.tsx";
import { Badge } from "./ui/badge.tsx";
import { Button } from "./ui/button.tsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card.tsx";
import { DataTable, features } from "./ui/data-table.tsx";
import { Input } from "./ui/input.tsx";
import { Label } from "./ui/label.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select.tsx";

const STATUS: Record<TradeStatus, { label: string; className: string }> = {
  PENDING: { label: "Pendente", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" },
  SETTLED: {
    label: "Liquidada",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  },
  CANCELLED: { label: "Cancelada", className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300" },
};

export function TradesPanel({ defaultFund }: { defaultFund: string }) {
  const notify = useNotify();
  const instruments = useInstruments();
  const trades = useTrades();
  const create = useCreateTrade();
  const transition = useTransitionTrade();
  const [form, setForm] = useState({
    instrument_id: "",
    fund_cnpj: defaultFund,
    trade_date: today(),
    side: "BUY" as TradeSide,
    quantity: "100",
    unit_price: "100.00",
  });

  const options = instruments.data?.items ?? [];
  const instrumentId = form.instrument_id || String(options[0]?.id ?? "");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    create.mutate(
      { ...form, instrument_id: Number(instrumentId), quantity: Number(form.quantity) },
      {
        onSuccess: (trade) => notify(`Boleta #${trade.id} registrada`),
        onError: (error) => notify(describeError(error), true),
      },
    );
  };

  const act = (id: number, action: "settle" | "cancel") =>
    transition.mutate(
      { id, action },
      {
        onSuccess: () => notify(action === "settle" ? `Boleta #${id} liquidada` : `Boleta #${id} cancelada`),
        onError: (error) => notify(describeError(error), true),
      },
    );

  const items = trades.data?.items ?? [];
  type Trade = (typeof items)[number];

  const helper = createColumnHelper<typeof features, Trade>();
  const columns = [
    helper.accessor("id", { header: "#", cell: (ctx) => <span className="text-muted-foreground">{ctx.getValue()}</span> }),
    helper.accessor("trade_date", { header: "Data", cell: (ctx) => <span className="whitespace-nowrap">{format.date(ctx.getValue())}</span> }),
    helper.accessor("cetip_code", { header: "Ativo", cell: (ctx) => <span className="font-mono text-[13px]">{ctx.getValue()}</span> }),
    helper.accessor("side", { header: "Lado", cell: (ctx) => (ctx.getValue() === "BUY" ? "Compra" : "Venda") }),
    helper.accessor("quantity", { header: "Qtd.", cell: (ctx) => <span className="tabular-nums">{format.quantity(ctx.getValue())}</span> }),
    helper.accessor("unit_price", { header: "Preço", cell: (ctx) => <span className="tabular-nums">{format.price(ctx.getValue())}</span> }),
    helper.accessor("status", {
      header: "Status",
      cell: (ctx) => {
        const status = STATUS[ctx.getValue() ?? "PENDING"];
        return <Badge className={status.className}>{status.label}</Badge>;
      },
    }),
    helper.display({
      id: "actions",
      cell: (ctx) =>
        ctx.row.original.status === "PENDING" ? (
          <div className="flex justify-end gap-1 whitespace-nowrap">
            <Button size="sm" disabled={transition.isPending} onClick={() => act(ctx.row.original.id, "settle")}>
              Liquidar
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={transition.isPending}
              onClick={() => act(ctx.row.original.id, "cancel")}
            >
              Cancelar
            </Button>
          </div>
        ) : null,
    }),
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Nova boleta</CardTitle>
          <CardDescription>O ativo é validado pelo instruments.public.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="instrument">Ativo</Label>
              <Select
                value={instrumentId}
                onValueChange={(v) => setForm({ ...form, instrument_id: v ?? "" })}
                disabled={options.length === 0}
              >
                <SelectTrigger id="instrument" className="w-full">
                  <SelectValue placeholder="Cadastre um ativo primeiro" />
                </SelectTrigger>
                <SelectContent>
                  {options.map((i) => (
                    <SelectItem key={i.id} value={String(i.id)}>
                      {i.cetip_code} · {i.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fund_cnpj">CNPJ do fundo</Label>
              <Input
                id="fund_cnpj"
                value={form.fund_cnpj}
                onChange={(e) => setForm({ ...form, fund_cnpj: e.target.value })}
                className="font-mono text-[13px]"
                inputMode="numeric"
                required
              />
              <span className="text-xs text-muted-foreground">14 dígitos, sem pontuação</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="trade_date">Data</Label>
                <Input
                  id="trade_date"
                  type="date"
                  value={form.trade_date}
                  onChange={(e) => setForm({ ...form, trade_date: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="side">Lado</Label>
                <Select value={form.side} onValueChange={(v) => v && setForm({ ...form, side: v as TradeSide })}>
                  <SelectTrigger id="side" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BUY">Compra</SelectItem>
                    <SelectItem value="SELL">Venda</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="quantity">Quantidade</Label>
                <Input
                  id="quantity"
                  type="number"
                  min={1}
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="unit_price">Preço unitário</Label>
                <Input
                  id="unit_price"
                  inputMode="decimal"
                  value={form.unit_price}
                  onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
                  required
                />
              </div>
            </div>
            <Button type="submit" disabled={create.isPending || options.length === 0}>
              {create.isPending ? "Registrando…" : "Registrar boleta"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Boletas</CardTitle>
          <CardDescription>Liquidar emite o TradeSettled, que o positions escuta.</CardDescription>
        </CardHeader>
        <CardContent>
          {trades.isLoading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Carregando…</p>
          ) : items.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Nenhuma boleta ainda.</p>
          ) : (
            <DataTable columns={columns} data={items} numericColumnIds={["quantity", "unit_price"]} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
