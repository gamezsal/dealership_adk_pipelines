import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 🟢 Proxy configuration: maps relative /api calls straight to FastAPI on port 8000
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
        // Keeps the /api prefix intact when forwarding to the backend
        rewrite: (path) => path,
      },
    },
  },
});