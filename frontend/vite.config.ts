/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Certs für HTTPS (mkcert generiert)
const certDir = path.resolve(__dirname, '../certs')
const certExists = fs.existsSync(path.join(certDir, 'cert.pem'))

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    // HTTPS aktivieren wenn Certs vorhanden
    ...(certExists ? {
      https: {
        key: fs.readFileSync(path.join(certDir, 'key.pem')),
        cert: fs.readFileSync(path.join(certDir, 'cert.pem')),
      }
    } : {}),
    // Proxy: Vite leitet WS + API intern weiter (nur für localhost-Dev)
    proxy: {
      '/api/ws': {
        target: 'ws://localhost:8765',
        ws: true,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/ws/, '/ws'),
      },
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    target: 'esnext',
    // Capacitor: relative Pfade für APK-Build
    ...(process.env.CAPACITOR_BUILD ? { base: './' } : {}),
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      reportOnFailure: true,
    },
  },
})
