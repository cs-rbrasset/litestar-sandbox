import type { AccountInfo } from "@azure/msal-browser";

import { acquireApiToken, login, msalInstance } from "./msal.ts";
import { client } from "#shared/api/generated/client.gen.ts";

// undefined: MSAL ainda não inicializou/processou o retorno do redirect. null: ninguém logado.
// $state de módulo: compartilhado por quem importa, reativo sem pub-sub manual (ao contrário
// da versão React, que precisa de useSyncExternalStore + CustomEvent).
let accountState = $state<AccountInfo | null | undefined>(undefined);

async function init(): Promise<void> {
  await msalInstance.initialize();
  await msalInstance.handleRedirectPromise();
  accountState = msalInstance.getAllAccounts()[0] ?? null;
}

export const auth = {
  get account() {
    return accountState;
  },
  init,
  signIn: login,
  signOut() {
    msalInstance.logoutRedirect();
  },
};

export function installAuth() {
  client.interceptors.request.use(async (request) => {
    const token = await acquireApiToken();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  });
}
