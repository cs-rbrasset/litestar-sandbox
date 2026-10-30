import { API_URL } from "$app/env/public";

import { installAuth } from "#shared/auth/index.ts";
import { client } from "./generated/client.gen.ts";

let configured = false;

/** Chamado do +layout.svelte, que reexecuta o <script> a cada instância (inclusive no SSR,
 * uma por request): a flag de módulo evita empilhar o mesmo interceptor várias vezes. */
export function configureApiClient(): void {
  if (configured) return;
  configured = true;
  // processo separado do Litestar: precisa de baseUrl e de CORS (core/app.py), ao contrário
  // da SPA em web/, que é servida pela própria API (mesma origem).
  client.setConfig({ baseUrl: API_URL });
  installAuth();
}
