import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import litestar from "litestar-vite-plugin";
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: Number(process.env.VITE_PORT || "5173"),
  },
  plugins: [
    tailwindcss(),
    react(),
    // lê o .litestar.json que a app escreve ao subir: asset url, bundle dir, tipos
    litestar({ input: ["src/main.tsx", "src/tailwind.css"], types: "auto" }),
  ],
  resolve: {
    alias: { "@": "/src" },
  },
});
