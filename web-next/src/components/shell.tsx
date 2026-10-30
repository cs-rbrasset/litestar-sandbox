"use client";

import { useMsal } from "@azure/msal-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "./ui/button.tsx";

const STEPS = [
  { href: "/", label: "Ativos", hint: "Cadastro por código CETIP" },
  { href: "/boletas", label: "Boletas", hint: "Registro e liquidação" },
  { href: "/posicoes", label: "Posições", hint: "Posição do fundo na data" },
] as const;

export function Shell({ children, name }: { children: ReactNode; name: string }) {
  const pathname = usePathname();
  const { instance } = useMsal();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-6 pt-6">
          <div className="pb-4">
            <p className="text-xs font-semibold tracking-widest text-brand-600 uppercase">POC Next.js</p>
            <h1 className="text-xl font-semibold">Do ativo à posição</h1>
          </div>
          <nav className="flex gap-1" aria-label="Etapas do fluxo">
            {STEPS.map((s, index) => {
              const active = pathname === s.href;
              return (
                <Link
                  key={s.href}
                  href={s.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2 border-b-2 px-4 pb-3 text-sm transition-colors ${
                    active
                      ? "border-brand-600 font-medium text-slate-900 dark:text-white"
                      : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                  }`}
                  title={s.hint}
                >
                  <span
                    className={`flex size-5 items-center justify-center rounded-full text-[11px] ${
                      active ? "bg-brand-600 text-white" : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {index + 1}
                  </span>
                  {s.label}
                </Link>
              );
            })}
          </nav>
          <div className="mb-3 flex items-center gap-3">
            <span className="text-sm text-slate-500">{name}</span>
            <Button variant="ghost" size="sm" onClick={() => instance.logoutRedirect()}>
              Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>

      <footer className="mx-auto max-w-6xl px-6 pb-8 text-xs text-slate-500">
        API em{" "}
        <a className="underline" href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/schema/swagger`}>
          /api/v1/schema
        </a>{" "}
        · cliente gerado do OpenAPI, direto do endpoint da API (sem litestar-vite)
      </footer>
    </div>
  );
}
