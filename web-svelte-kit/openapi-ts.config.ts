import { defineConfig } from "@hey-api/openapi-ts";

// Independente do litestar-vite: lê o schema direto da API rodando (sem bundler no meio),
// igual o web-next.
export default defineConfig({
  input: process.env.OPENAPI_URL ?? "http://localhost:8000/api/v1/schema/openapi.json",
  output: "./src/shared/api/generated",
  plugins: ["@hey-api/typescript", "@hey-api/schemas", "@hey-api/sdk", "@hey-api/client-fetch"],
});
