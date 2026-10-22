import { useState, type FormEvent } from "react";

import { auth } from "../auth.ts";
import { apiV1InstrumentsListInstruments } from "../generated/api/sdk.gen.ts";
import { Button, Field, Input } from "./ui.tsx";

export function SignIn() {
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setChecking(true);
    setError(null);
    // confere o token antes de entrar: uma leitura qualquer da API
    const { response } = await apiV1InstrumentsListInstruments({
      query: { pageSize: 1 },
      headers: { Authorization: `Bearer ${token}` },
    });
    setChecking(false);
    if (response?.ok) {
      auth.signIn(token);
    } else if (response?.status === 401) {
      setError("Token não reconhecido pela API.");
    } else {
      setError(response ? `Erro ${response.status}.` : "A API não respondeu.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <form
        onSubmit={submit}
        className="flex w-full max-w-sm flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <div>
          <p className="text-xs font-semibold tracking-widest text-brand-600 uppercase">POC Litestar</p>
          <h1 className="mt-1 text-xl font-semibold">Entrar</h1>
          <p className="mt-1 text-sm text-slate-500">
            Ambiente de desenvolvimento: use um token de <code>AUTH_DEV_TOKENS</code>. Em produção, o login é
            pelo Entra ID.
          </p>
        </div>
        <Field label="Token">
          <Input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
            autoFocus
            required
          />
        </Field>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <Button type="submit" disabled={checking || token === ""}>
          {checking ? "Conferindo…" : "Entrar"}
        </Button>
      </form>
    </div>
  );
}
