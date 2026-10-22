import { client } from "./generated/api/client.gen.ts";

// Token de desenvolvimento (DevTokenVerifier). Com o Entra ID, a sessão passa a viver num
// cookie httpOnly emitido pela API, e esta parte deixa de existir no front.
const KEY = "api-token";
const CHANGED = "auth-changed";

export const auth = {
  token: () => sessionStorage.getItem(KEY),
  signIn: (token: string) => {
    sessionStorage.setItem(KEY, token);
    window.dispatchEvent(new Event(CHANGED));
  },
  signOut: () => {
    sessionStorage.removeItem(KEY);
    window.dispatchEvent(new Event(CHANGED));
  },
  subscribe: (onChange: () => void) => {
    window.addEventListener(CHANGED, onChange);
    return () => window.removeEventListener(CHANGED, onChange);
  },
};

export function installAuth() {
  client.interceptors.request.use((request) => {
    const token = auth.token();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  });
  client.interceptors.response.use((response) => {
    // token expirado ou revogado: volta para a tela de entrada
    if (response.status === 401 && auth.token()) {
      auth.signOut();
    }
    return response;
  });
}
