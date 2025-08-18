// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ command, mode }) => {
  return {
    plugins: [vue()],
    base: '/',  // 👈 absolute path instead of './'
    server: {
      proxy: command === 'serve' ? {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      } : undefined
    }
  }
})
