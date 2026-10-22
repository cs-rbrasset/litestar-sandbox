import { useState } from "react";

import { describeError, format, today } from "../api.ts";
import { usePositions } from "../queries.ts";
import { Card, Empty, Field, Input, mono, Table } from "./ui.tsx";

export function PositionsPanel({ defaultFund }: { defaultFund: string }) {
  const [fund, setFund] = useState(defaultFund);
  const [date, setDate] = useState(today());
  const positions = usePositions(fund, date);
  const items = positions.data ?? [];
  const validFund = /^\d{14}$/.test(fund);

  return (
    <Card
      title="Posição do fundo"
      description="Soma das movimentações liquidadas até a data, sem as posições zeradas."
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-[1fr_12rem]">
        <Field label="CNPJ do fundo" hint={validFund ? format.cnpj(fund) : "14 dígitos, sem pontuação"}>
          <Input value={fund} onChange={(e) => setFund(e.target.value)} className={mono} inputMode="numeric" />
        </Field>
        <Field label="Data de referência">
          <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </Field>
      </div>

      {!validFund ? (
        <Empty>Informe um CNPJ com 14 dígitos.</Empty>
      ) : positions.isError ? (
        <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm whitespace-pre-line text-rose-700 dark:bg-rose-950 dark:text-rose-300">
          {describeError(positions.error)}
        </p>
      ) : positions.isLoading ? (
        <Empty>Carregando…</Empty>
      ) : items.length === 0 ? (
        <Empty>Sem posição em {format.date(date)}.</Empty>
      ) : (
        <Table head={["Ativo", "Quantidade"]} numeric={["Quantidade"]}>
          {items.map((p) => (
            <tr key={p.instrument_id}>
              <td className={`px-3 py-2.5 ${mono}`}>{p.cetip_code}</td>
              <td
                className={`px-3 py-2.5 text-right font-medium tabular-nums ${p.quantity < 0 ? "text-rose-600" : ""}`}
              >
                {format.quantity(p.quantity)}
              </td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}
