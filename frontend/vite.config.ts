import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // NEW: Silently append the trailing slash so FastAPI receives 
        // the exact path it expects, completely bypassing the 307 Redirect!
        rewrite: (path) => path.replace(/^\/api\/copilotkit\/?$/, '/api/copilotkit/')
      }
    }
  }
})