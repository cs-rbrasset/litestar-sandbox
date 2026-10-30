import { PublicClientApplication, type Configuration } from "@azure/msal-browser";

// Cliente público (SPA, PKCE, sem secret) — o backend nunca participa do login, só valida
// o id_token (core/auth.py, EntraTokenVerifier) contra o JWKS do tenant.

// Sem "Expose an API" no App registration (exige acesso de admin no Entra que não temos
// aqui), não existe scope próprio pra pedir access token — scope default (Graph) é o que
// sobra. O id_token, esse sim, sempre tem "aud" = o próprio client_id, sem exposição nenhuma.
const LOGIN_SCOPES = ["User.Read"];

const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID ?? "",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID ?? ""}`,
    redirectUri: window.location.origin,
  },
  cache: { cacheLocation: "sessionStorage" },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export function login(): void {
  msalInstance.loginRedirect({ scopes: LOGIN_SCOPES });
}

/** id_token pra chamar a API (aud = client_id, validado em core/entra.py). null: ninguém logado. */
export async function acquireApiToken(): Promise<string | null> {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) return null;
  try {
    const result = await msalInstance.acquireTokenSilent({ scopes: LOGIN_SCOPES, account });
    return result.idToken;
  } catch {
    // refresh falhou de verdade (não é só "ninguém logado ainda"): manda renovar a sessão
    await msalInstance.acquireTokenRedirect({ scopes: LOGIN_SCOPES });
    return null;
  }
}
