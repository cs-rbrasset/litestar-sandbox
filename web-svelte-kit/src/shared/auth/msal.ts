import { ENTRA_CLIENT_ID, ENTRA_TENANT_ID } from "$app/env/public";
import { PublicClientApplication, type Configuration } from "@azure/msal-browser";

// Cliente público (SPA, PKCE, sem secret) — o backend nunca participa do login, só valida
// o access_token (core/auth.py, EntraTokenVerifier) contra o JWKS do tenant.

// App registration com "Expose an API" feito (scope access_as_user): o access_token pedido
// com esse scope tem "aud" = o próprio client_id (manifest v2), igual ENTRA_API_AUDIENCE.
const LOGIN_SCOPES = [`api://${ENTRA_CLIENT_ID}/access_as_user`];

const msalConfig: Configuration = {
  auth: {
    clientId: ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${ENTRA_TENANT_ID}`,
    redirectUri: typeof window === "undefined" ? undefined : window.location.origin,
  },
  cache: { cacheLocation: "sessionStorage" },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export function login(): void {
  msalInstance.loginRedirect({ scopes: LOGIN_SCOPES });
}

/** access_token pra chamar a API (aud = client_id, validado em core/entra.py). null: ninguém logado. */
export async function acquireApiToken(): Promise<string | null> {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) return null;
  try {
    const result = await msalInstance.acquireTokenSilent({ scopes: LOGIN_SCOPES, account });
    return result.accessToken;
  } catch {
    // refresh falhou de verdade (não é só "ninguém logado ainda"): manda renovar a sessão
    await msalInstance.acquireTokenRedirect({ scopes: LOGIN_SCOPES });
    return null;
  }
}
