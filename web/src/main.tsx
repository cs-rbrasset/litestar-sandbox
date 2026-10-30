import { MsalProvider } from "@azure/msal-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.tsx";
import { installAuth } from "./auth.ts";
import { client } from "./generated/api/client.gen.ts";
import { ToastProvider } from "./components/toast.tsx";
import { msalInstance } from "./msal.ts";

// A SPA é servida pela própria API: mesma origem, sem baseUrl nem CORS.
client.setConfig({ baseUrl: "" });
installAuth();

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

const root = document.getElementById("root");
if (root === null) {
  throw new Error("Root element #root not found");
}

// o SDK do MSAL processa o retorno do redirect de login antes de qualquer coisa renderizar
await msalInstance.initialize();
await msalInstance.handleRedirectPromise();

createRoot(root).render(
  <StrictMode>
    <MsalProvider instance={msalInstance}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <App />
        </ToastProvider>
      </QueryClientProvider>
    </MsalProvider>
  </StrictMode>,
);
