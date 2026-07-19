import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    minify: false,
    cssCodeSplit: false,
  },
  server: {
    // Forward API + WebSocket calls to the FastAPI backend during local dev,
    // so the frontend can use same-origin relative URLs (/api) that also work
    // when FastAPI serves the built SPA in production.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
