// Plugins
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import ViteFonts from 'unplugin-fonts/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    basicSsl(),
    vue({
      template: { transformAssetUrls },
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    ViteFonts({
      google: {
        families: [
          {
            name: 'Roboto',
            styles: 'wght@100;300;400;500;700;900',
          },
        ],
      },
    }),
  ],
  base: process.env.NODE_ENV === 'production' ? '/new-admin/' : '/',
  define: { 'process.env': {}, __VUE_OPTIONS_API__: false },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    extensions: ['.js', '.json', '.jsx', '.mjs', '.ts', '.tsx', '.vue'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target:
          process.env.DOCKER == 'yes'
            ? 'https://api:8000'
            : 'http://127.0.0.1:8000',
        secure: false,
      },
    },
    https: true,
    cors: {
      origin: '*',
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: ['X-Requested-With', 'content-type', 'Authorization'],
    },
  },
  build: {
    emptyOutDir: true,
    outDir: '../modoboa/frontend_dist',
  },
})
