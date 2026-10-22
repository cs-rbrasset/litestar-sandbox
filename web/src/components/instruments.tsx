import { useState, type FormEvent } from "react";

import { describeError } from "../api.ts";
import type { InstrumentType } from "../generated/api/types.gen.ts";
import { useArchiveInstrument, useCreateInstrument, useInstruments } from "../queries.ts";
import { useNotify } from "./toast.tsx";
import { Badge, Button, Card, Empty, Field, Input, mono, Select, Table } from "./ui.tsx";

const TYPES: InstrumentType[] = ["CRI", "DEB", "CDB", "LCI"];

export function InstrumentsPanel() {
  const notify = useNotify();
  const instruments = useInstruments();
  const create = useCreateInstrument();
  const archive = useArchiveInstrument();
  const [form, setForm] = useState({ name: "", cetip_code: "", instrument_type: "CRI" as InstrumentType });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    create.mutate(form, {
      onSuccess: (created) => {
        notify(`Ativo ${created.cetip_code} cadastrado`);
        setForm({ ...form, name: "", cetip_code: "" });
      },
      onError: (error) => notify(describeError(error), true),
    });
  };

  const items = instruments.data?.items ?? [];

  return (
    <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <Card title="Novo ativo" description="O código CETIP é normalizado para maiúsculas.">
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label="Nome">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </Field>
          <Field label="Código CETIP" hint="4 a 20 letras ou números">
            <Input
              value={form.cetip_code}
              onChange={(e) => setForm({ ...form, cetip_code: e.target.value })}
              className={mono}
              required
            />
          </Field>
          <Field label="Tipo">
            <Select
              value={form.instrument_type}
              onChange={(e) => setForm({ ...form, instrument_type: e.target.value as InstrumentType })}
            >
              {TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </Select>
          </Field>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Salvando…" : "Cadastrar ativo"}
          </Button>
        </form>
      </Card>

      <Card
        title="Ativos cadastrados"
        description={`${instruments.data?.total ?? 0} em uso; os arquivados não aparecem`}
      >
        {instruments.isLoading ? (
          <Empty>Carregando…</Empty>
        ) : items.length === 0 ? (
          <Empty>Nenhum ativo ainda. Cadastre o primeiro ao lado.</Empty>
        ) : (
          <Table head={["Código", "Nome", "Tipo", ""]}>
            {items.map((item) => (
              <tr key={item.id}>
                <td className={`px-3 py-2.5 ${mono}`}>{item.cetip_code}</td>
                <td className="px-3 py-2.5">{item.name}</td>
                <td className="px-3 py-2.5">
                  <Badge tone="brand">{item.instrument_type}</Badge>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={archive.isPending}
                    onClick={() =>
                      archive.mutate(item.id, {
                        onSuccess: () => notify(`Ativo ${item.cetip_code} arquivado`),
                        onError: (error) => notify(describeError(error), true),
                      })
                    }
                  >
                    Arquivar
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}
