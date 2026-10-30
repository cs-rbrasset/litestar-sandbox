import { login } from "../msal.ts";
import { Button } from "./ui.tsx";

export function SignIn() {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="flex w-full max-w-sm flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div>
          <p className="text-xs font-semibold tracking-widest text-brand-600 uppercase">POC Litestar</p>
          <h1 className="mt-1 text-xl font-semibold">Entrar</h1>
          <p className="mt-1 text-sm text-slate-500">
            Login via Entra ID direto no navegador (MSAL.js, PKCE) — o token nunca passa pelo
            backend, só é enviado pra API já pronto.
          </p>
        </div>
        <Button type="button" onClick={login}>
          Entrar com Microsoft
        </Button>
      </div>
    </div>
  );
}
