import { useState, type FormEvent } from "react";

import { describeError, format, today } from "../api.ts";
import type { TradeSide, TradeStatus } from "../generated/api/types.gen.ts";
import { useCreateTrade, useInstruments, useTrades, useTransitionTrade } from "../queries.ts";
import { useNotify } from "./toast.tsx";
import { Badge, Button, Card, Empty, Field, Input, mono, Select, Table } from "./ui.tsx";

const STATUS: Record<TradeStatus, { label: string; tone: "amber" | "emerald" | "slate" }> = {
  PENDING: { label: "Pendente", tone: "amber" },
  SETTLED: { label: "Liquidada", tone: "emerald" },
  CANCELLED: { label: "Cancelada", tone: "slate" },
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

  return (
    <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <Card title="Nova boleta" description="O ativo é validado pelo instruments.public.">
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label="Ativo">
            <Select
              value={instrumentId}
              onChange={(e) => setForm({ ...form, instrument_id: e.target.value })}
              required
            >
              {options.length === 0 && <option value="">Cadastre um ativo primeiro</option>}
              {options.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.cetip_code} · {i.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="CNPJ do fundo" hint="14 dígitos, sem pontuação">
            <Input
              value={form.fund_cnpj}
              onChange={(e) => setForm({ ...form, fund_cnpj: e.target.value })}
              className={mono}
              inputMode="numeric"
              required
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Data">
              <Input
                type="date"
                value={form.trade_date}
                onChange={(e) => setForm({ ...form, trade_date: e.target.value })}
                required
              />
            </Field>
            <Field label="Lado">
              <Select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as TradeSide })}>
                <option value="BUY">Compra</option>
                <option value="SELL">Venda</option>
              </Select>
            </Field>
            <Field label="Quantidade">
              <Input
                type="number"
                min={1}
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                required
              />
            </Field>
            <Field label="Preço unitário">
              <Input
                inputMode="decimal"
                value={form.unit_price}
                onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
                required
              />
            </Field>
          </div>
          <Button type="submit" disabled={create.isPending || options.length === 0}>
            {create.isPending ? "Registrando…" : "Registrar boleta"}
          </Button>
        </form>
      </Card>

      <Card title="Boletas" description="Liquidar emite o TradeSettled, que o positions escuta.">
        {trades.isLoading ? (
          <Empty>Carregando…</Empty>
        ) : items.length === 0 ? (
          <Empty>Nenhuma boleta ainda.</Empty>
        ) : (
          <Table head={["#", "Data", "Ativo", "Lado", "Qtd.", "Preço", "Status", ""]} numeric={["Qtd.", "Preço"]}>
            {items.map((t) => {
              const status = STATUS[t.status ?? "PENDING"];
              return (
                <tr key={t.id}>
                  <td className="px-3 py-2.5 text-slate-500">{t.id}</td>
                  <td className="px-3 py-2.5 whitespace-nowrap">{format.date(t.trade_date)}</td>
                  <td className={`px-3 py-2.5 ${mono}`}>{t.cetip_code}</td>
                  <td className="px-3 py-2.5">{t.side === "BUY" ? "Compra" : "Venda"}</td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{format.quantity(t.quantity)}</td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{format.price(t.unit_price)}</td>
                  <td className="px-3 py-2.5">
                    <Badge tone={status.tone}>{status.label}</Badge>
                  </td>
                  <td className="px-3 py-2.5 text-right whitespace-nowrap">
                    {t.status === "PENDING" && (
                      <span className="inline-flex gap-1">
                        <Button size="sm" disabled={transition.isPending} onClick={() => act(t.id, "settle")}>
                          Liquidar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={transition.isPending}
                          onClick={() => act(t.id, "cancel")}
                        >
                          Cancelar
                        </Button>
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </Table>
        )}
      </Card>
    </div>
  );
}
