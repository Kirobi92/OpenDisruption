import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Tauri erwartet einen festen Port
  server: {
    port: 1420,
    strictPort: true,
    // Proxy für lokalen Kirobi-Stack (Entwicklung)
    proxy: {
      '/api': {
        target: 'http://kirobi.local',
        changeOrigin: true,
      },
    },
  },

  // Tauri-Build: keine Basis-URL, relative Pfade
  base: './',

  build: {
    // Tauri unterstützt ES2021+
    target: ['es2021', 'chrome100', 'safari13'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
    outDir: 'dist',
  },

  // Umgebungsvariablen mit VITE_ Prefix
  envPrefix: ['VITE_', 'TAURI_'],
});
