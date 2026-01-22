import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api-backend': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api-backend/, '')
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: [
      'smartbuddy-web-production.up.railway.app',
      '.railway.app'
    ]
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    minify: 'terser',
    sourcemap: false
  }
})
