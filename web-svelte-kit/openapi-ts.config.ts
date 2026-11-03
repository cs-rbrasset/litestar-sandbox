import { defineConfig } from "@hey-api/openapi-ts";

// Independente do litestar-vite: lê o schema direto da API rodando (sem bundler no meio),
// igual o web-next.
// tsconfig.json usa "extends": "$app/tsconfig" (alias do SvelteKit, resolvido pelo
// svelte-check); o parser de tsconfig do openapi-ts@0.99.0 não conhece esse alias e falha
// ao tentar carregá-lo (tsConfigPath: null desliga a leitura). O campo existe em runtime
// mas falta no .d.ts dessa versão — daqui o `as never` só pra calar o typecheck.
export default defineConfig({
  input: process.env.OPENAPI_URL ?? "http://localhost:8000/api/v1/schema/openapi.json",
  output: "./src/shared/api/generated",
  plugins: ["@hey-api/typescript", "@hey-api/schemas", "@hey-api/sdk", "@hey-api/client-fetch"],
  tsConfigPath: null,
} as Parameters<typeof defineConfig>[0] & { tsConfigPath: null });
