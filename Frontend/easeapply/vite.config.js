// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ command, mode }) => {
  return {
    plugins: [vue()],
    base: './',
    server: {
      // Only use proxy in development mode
      proxy: command === 'serve' ? {
        '/api': {
          target: 'http://localhost:8000', // Only for local development
          changeOrigin: true,
          secure: false,
        }
      } : undefined
    }
  }
})
