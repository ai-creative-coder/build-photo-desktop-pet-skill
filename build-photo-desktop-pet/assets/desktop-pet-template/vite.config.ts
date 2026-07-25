import { cp, mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const releasePetAssets = resolve(__dirname, "public/assets/pet/integrated-v1");
const releaseAssetOutput = resolve(__dirname, "dist/assets/pet/integrated-v1");

function copyReleasePetAssets(): Plugin {
  return {
    name: "copy-release-pet-assets",
    apply: "build",
    async writeBundle() {
      await mkdir(releaseAssetOutput, { recursive: true });
      await cp(releasePetAssets, releaseAssetOutput, { recursive: true });
    },
  };
}

export default defineConfig({
  base: "./",
  publicDir: false,
  plugins: [react(), copyReleasePetAssets()],
  build: {
    target: "es2020",
    minify: "esbuild",
    sourcemap: false,
  },
});
