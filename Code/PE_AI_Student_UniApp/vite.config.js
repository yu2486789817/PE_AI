import { defineConfig } from 'vite';
import uni from '@dcloudio/vite-plugin-uni';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [
    uni(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/User': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/Class': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/Course': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/Homework': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/video': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/video/, '')
      },
      '/chat': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/chat/, '')
      }
    }
  }
});
