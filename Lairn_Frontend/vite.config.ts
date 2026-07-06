// Configuración de Vite (bundler de desarrollo y producción).
// Plugins: React (JSX/refresh) + Tailwind CSS v4 (procesado de estilos).
// Alias: @/ apunta a ./src/ para imports limpios.
//
// Optimizaciones de build:
//   - target: baseline-widely-available → código compatible con navegadores modernos sin polyfills innecesarios.
//   - manualChunks: separa vendor libs en chunks independientes para mejor cache.
//   - chunkSizeWarningLimit: 500 KB como límite antes de advertir.
//   - sourcemap: desactivado en producción (más rápido, menos exposición).
//
// Optimizaciones de desarrollo:
//   - optimizeDeps.include: pre-bundlea dependencias pesadas para arrancar más rápido.
//   - server.port: puerto fijo para consistencia del equipo.
//   - hmr.overlay: muestra errores de HMR como overlay visual.

import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  build: {
    target: 'baseline-widely-available',
    sourcemap: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') && !id.includes('react-router')) return 'vendor'
            if (id.includes('recharts')) return 'charts'
            if (id.includes('react-hook-form') || id.includes('@hookform') || id.includes('zod')) return 'forms'
            if (id.includes('react-router')) return 'router'
          }
        },
      },
    },
  },

  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios', 'recharts'],
  },

  server: {
    port: 5173,
    hmr: {
      overlay: true,
    },
  },
})
