// vite.config.js
export default defineConfig({
  plugins: [vue()],
  base: './', // Add this for correct asset paths
  server: {
    proxy: {
      '/api': {
        target: import.meta.env.PROD 
          ? 'https://easeapply.onrender.com' 
          : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})
