import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import ElementPlus from 'unplugin-element-plus/vite'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    ElementPlus(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5300,
    proxy: {
      '/User': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/Class': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/Course': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/Course_student': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/Homework': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/video': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/chat': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      },
      '/Teaching-video': {
        target: 'https://pe-ai-backend-9869.onrender.com',
        changeOrigin: true,
        secure: false
      }


    }
  }
})
