import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  if (!env.VITE_API_URL?.trim()) {
    throw new Error(
      "VITE_API_URL no está configurada. Defina la URL del backend para compilar el frontend.",
    );
  }

  return {
    plugins: [react()],
  };
});
