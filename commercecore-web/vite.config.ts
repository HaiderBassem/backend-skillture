/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// The API has no CORS headers, so in development the browser talks to this server's
// /api path and Vite forwards it to FastAPI (stripping the /api prefix).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.API_PROXY_TARGET || "http://127.0.0.1:8000";
  const proxy = {
    "/api": { target, changeOrigin: true, rewrite: (path: string) => path.replace(/^\/api/, "") },
  };
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: { port: 5173, proxy },
    preview: { port: 5173, proxy },
    test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], globals: true },
  };
});
