import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  envDir: '../',
  envPrefix: ['VITE_', 'GEMINI_'],
  server: {
    host: true,
    
    proxy: {
      '/api': {
        target: 'http://localhost:8012',
        changeOrigin: true,
        secure: false,
      },
      '/ollama-api': {
        target: 'http://localhost:11434',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ollama-api/, '/api')
      }
    }
  }
})
