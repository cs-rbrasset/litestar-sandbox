import { defineEnvVars } from "@sveltejs/kit/env";

// Processo separado do Litestar (sem litestar-vite): precisa saber onde a API está.
export const variables = defineEnvVars({
  API_URL: { public: true, description: "Base URL da API Litestar" },
  ENTRA_CLIENT_ID: { public: true, description: "App registration SPA do Entra ID" },
  ENTRA_TENANT_ID: { public: true, description: "Tenant do Entra ID" },
});
