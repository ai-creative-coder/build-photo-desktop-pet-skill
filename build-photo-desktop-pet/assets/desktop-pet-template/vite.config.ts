import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  publicDir: "public",
  plugins: [react()],
  build: {
    target: "es2020",
    minify: "esbuild",
    sourcemap: false,
  },
});
