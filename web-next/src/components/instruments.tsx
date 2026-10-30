"use client";

import { useState, type FormEvent } from "react";

import { createColumnHelper } from "@tanstack/react-table";

import { describeError } from "../api.ts";
import type { InstrumentType } from "../generated/api/types.gen.ts";
import { useArchiveInstrument, useCreateInstrument, useInstruments } from "../queries.ts";
import { useNotify } from "./toast.tsx";
import { Badge } from "./ui/badge.tsx";
import { Button } from "./ui/button.tsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card.tsx";
import { DataTable, features } from "./ui/data-table.tsx";
import { Input } from "./ui/input.tsx";
import { Label } from "./ui/label.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select.tsx";

const TYPES: InstrumentType[] = ["CRI", "DEB", "CDB", "LCI"];

type Instrument = {
  id: number;
  cetip_code: string;
  name: string;
  instrument_type: InstrumentType;
};

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

  const helper = createColumnHelper<typeof features, Instrument>();
  const columns = [
    helper.accessor("cetip_code", { header: "Código", cell: (ctx) => <span className="font-mono text-[13px]">{ctx.getValue()}</span> }),
    helper.accessor("name", { header: "Nome" }),
    helper.accessor("instrument_type", {
      header: "Tipo",
      cell: (ctx) => (
        <Badge className="bg-brand-100 text-brand-700 dark:bg-brand-700/30 dark:text-brand-100">
          {ctx.getValue()}
        </Badge>
      ),
    }),
    helper.display({
      id: "actions",
      cell: (ctx) => (
        <div className="text-right">
          <Button
            variant="destructive"
            size="sm"
            disabled={archive.isPending}
            onClick={() =>
              archive.mutate(ctx.row.original.id, {
                onSuccess: () => notify(`Ativo ${ctx.row.original.cetip_code} arquivado`),
                onError: (error) => notify(describeError(error), true),
              })
            }
          >
            Arquivar
          </Button>
        </div>
      ),
    }),
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Novo ativo</CardTitle>
          <CardDescription>O código CETIP é normalizado para maiúsculas.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cetip_code">Código CETIP</Label>
              <Input
                id="cetip_code"
                value={form.cetip_code}
                onChange={(e) => setForm({ ...form, cetip_code: e.target.value })}
                className="font-mono text-[13px]"
                required
              />
              <span className="text-xs text-muted-foreground">4 a 20 letras ou números</span>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="instrument_type">Tipo</Label>
              <Select
                value={form.instrument_type}
                onValueChange={(v) => v && setForm({ ...form, instrument_type: v as InstrumentType })}
              >
                <SelectTrigger id="instrument_type" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Salvando…" : "Cadastrar ativo"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ativos cadastrados</CardTitle>
          <CardDescription>{`${instruments.data?.total ?? 0} em uso; os arquivados não aparecem`}</CardDescription>
        </CardHeader>
        <CardContent>
          {instruments.isLoading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Carregando…</p>
          ) : items.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Nenhum ativo ainda. Cadastre o primeiro ao lado.
            </p>
          ) : (
            <DataTable columns={columns} data={items} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
