import adapter from "@sveltejs/adapter-auto";
import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: Number(process.env.VITE_PORT || "5173"),
  },
  plugins: [
    tailwindcss(),
    // SvelteKit 3: a config que antes vivia em svelte.config.js vai direto aqui
    sveltekit({
      adapter: adapter(),
      // Feature-Sliced Design: routing do SvelteKit mora dentro da camada app/,
      // pages/ fica livre pro layer da FSD (guia oficial fsd.how para SvelteKit).
      // Alias por subpath imports do package.json (ver "imports" lá), não kit.alias:
      // SvelteKit 3 deprecou config.alias a favor de subpath imports nativo do Node.
      files: {
        routes: "src/app/routes",
        appTemplate: "src/app/app.html",
      },
    }),
  ],
});
