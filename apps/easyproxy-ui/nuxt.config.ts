export default defineNuxtConfig({
  devtools: { enabled: true },
  ssr: false,
  modules: ['@pinia/nuxt'],
  devServer: {
    port: 3002,
  },
  vite: {
    server: {
      proxy: {
        '/api': { target: 'http://localhost:8000', changeOrigin: true },
        '/ws': { target: 'ws://localhost:8000', ws: true },
      },
    },
  },
  css: ['~/assets/css/main.css'],
})
