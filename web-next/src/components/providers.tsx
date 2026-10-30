"use client";

import { MsalProvider, useIsAuthenticated, useMsal } from "@azure/msal-react";
import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { installAuth } from "../auth.ts";
import { client } from "../generated/api/client.gen.ts";
import { msalInstance } from "../msal.ts";
import { Shell } from "./shell.tsx";
import { SignIn } from "./sign-in.tsx";
import { ToastProvider } from "./toast.tsx";

// Processo separado do Litestar: precisa de baseUrl e de CORS (core/app.py), ao contrário
// da SPA em web/, que é servida pela própria API (mesma origem).
client.setConfig({ baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000" });

let authInstalled = false;
function installAuthOnce() {
  if (authInstalled) return;
  authInstalled = true;
  installAuth();
}
installAuthOnce();

export function Providers({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } }),
  );

  // o SDK do MSAL processa o retorno do redirect de login antes de qualquer coisa renderizar
  useEffect(() => {
    msalInstance
      .initialize()
      .then(() => msalInstance.handleRedirectPromise())
      .finally(() => setReady(true));
  }, []);

  if (!ready) return null;

  return (
    <MsalProvider instance={msalInstance}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AuthGate>{children}</AuthGate>
        </ToastProvider>
      </QueryClientProvider>
    </MsalProvider>
  );
}

function AuthGate({ children }: { children: ReactNode }) {
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
  return <Shell name={accounts[0]?.name ?? accounts[0]?.username ?? ""}>{children}</Shell>;
}
