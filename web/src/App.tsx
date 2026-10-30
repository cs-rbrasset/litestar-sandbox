import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { InstrumentsPanel } from "./components/instruments.tsx";
import { PositionsPanel } from "./components/positions.tsx";
import { SignIn } from "./components/sign-in.tsx";
import { TradesPanel } from "./components/trades.tsx";
import { Button } from "./components/ui.tsx";

const DEFAULT_FUND = "12345678000190";

const STEPS = [
  { id: "ativos", label: "Ativos", hint: "Cadastro por código CETIP" },
  { id: "boletas", label: "Boletas", hint: "Registro e liquidação" },
  { id: "posicoes", label: "Posições", hint: "Posição do fundo na data" },
] as const;

type StepId = (typeof STEPS)[number]["id"];

// a aba vive na URL (/ativos, /boletas, /posicoes): o fallback da SPA serve qualquer caminho
const fromPath = (): StepId => STEPS.find((s) => location.pathname === `/${s.id}`)?.id ?? "ativos";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const { accounts } = useMsal();
  const queryClient = useQueryClient();

  // ao sair, nada do usuário anterior fica no cache
  useEffect(() => {
    if (!isAuthenticated) {
      queryClient.clear();
    }
  }, [isAuthenticated, queryClient]);

  if (!isAuthenticated) return <SignIn />;
  return <Workspace name={accounts[0]?.name ?? accounts[0]?.username ?? ""} />;
}

function Workspace({ name }: { name: string }) {
  const { instance } = useMsal();
  const [step, setStep] = useState<StepId>(fromPath);

  useEffect(() => {
    const onPop = () => setStep(fromPath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const go = (id: StepId) => {
    history.pushState(null, "", `/${id}`);
    setStep(id);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-6 pt-6">
          <div className="pb-4">
            <p className="text-xs font-semibold tracking-widest text-brand-600 uppercase">POC Litestar</p>
            <h1 className="text-xl font-semibold">Do ativo à posição</h1>
          </div>
          <nav className="flex gap-1" aria-label="Etapas do fluxo">
            {STEPS.map((s, index) => (
              <button
                key={s.id}
                onClick={() => go(s.id)}
                aria-current={step === s.id ? "page" : undefined}
                className={`flex items-center gap-2 border-b-2 px-4 pb-3 text-sm transition-colors ${
                  step === s.id
                    ? "border-brand-600 font-medium text-slate-900 dark:text-white"
                    : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
                title={s.hint}
              >
                <span
                  className={`flex size-5 items-center justify-center rounded-full text-[11px] ${
                    step === s.id ? "bg-brand-600 text-white" : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                  }`}
                >
                  {index + 1}
                </span>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="mb-3 flex items-center gap-3">
            <span className="text-sm text-slate-500">{name}</span>
            <Button variant="ghost" size="sm" onClick={() => instance.logoutRedirect()}>
              Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {step === "ativos" && <InstrumentsPanel />}
        {step === "boletas" && <TradesPanel defaultFund={DEFAULT_FUND} />}
        {step === "posicoes" && <PositionsPanel defaultFund={DEFAULT_FUND} />}
      </main>

      <footer className="mx-auto max-w-6xl px-6 pb-8 text-xs text-slate-500">
        API em <a className="underline" href="/api/v1/schema/swagger">/api/v1/schema</a> · cliente gerado do
        OpenAPI pelo litestar-vite
      </footer>
    </div>
  );
}
