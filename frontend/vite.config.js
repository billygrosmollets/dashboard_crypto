import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  // Production build configuration
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',  // Use esbuild (default, faster than terser)
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'axios-vendor': ['axios']
        }
      }
    }
  },

  // Development server (proxy only in dev mode)
  server: {
    port: 5173,
    proxy: {
      // Proxy API requests to Flask backend
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
