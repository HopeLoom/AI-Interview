import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  // Vite automatically loads environment files in this order:
  // 1. .env.${mode}.${NODE_ENV} (e.g., .env.candidate-practice.production)
  // 2. .env.${mode} (e.g., .env.candidate-practice)
  // 3. .env.${NODE_ENV} (e.g., .env.production)
  // 4. .env (base environment)
  
  return {
    plugins: [
      react(),
    ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "client", "src"),
      "@shared": path.resolve(__dirname, "shared"),
      "@assets": path.resolve(__dirname, "attached_assets"),
    },
  },
  root: path.resolve(__dirname, "client"),
    build: {
      outDir: path.resolve(__dirname, "dist/public"),
      emptyOutDir: true,
    },
  };
});
