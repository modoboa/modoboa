// Plugins
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import ViteFonts from 'unplugin-fonts/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { federation } from '@module-federation/vite'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// @module-federation/vite emits its bootstrap shim files via emitFile() with
// an explicit `fileName`, which bypasses Rollup's entry/asset naming patterns
// and dumps them at the bundle root. Relocate them under assets/ so the
// produced layout matches the rest of the build (single canonical asset
// directory for collectstatic / CDN sync).
function relocateMfBootstrap() {
  return {
    name: 'modoboa-relocate-mf-bootstrap',
    enforce: 'post',
    generateBundle(_options, bundle) {
      const moved = new Map()
      for (const fileName of Object.keys(bundle)) {
        if (fileName.startsWith('mf-entry-bootstrap-')) {
          const newName = `assets/${fileName}`
          bundle[fileName].fileName = newName
          bundle[newName] = bundle[fileName]
          delete bundle[fileName]
          moved.set(fileName, newName)
        }
      }
      for (const asset of Object.values(bundle)) {
        if (asset.type === 'asset' && asset.fileName.endsWith('.html')) {
          let html = asset.source.toString()
          for (const [oldName, newName] of moved) {
            html = html.split(`/${oldName}`).join(`/${newName}`)
          }
          asset.source = html
        }
      }
    },
  }
}

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
    federation({
      name: 'modoboa_host',
      filename: 'remoteEntry.js',
      // JS-only project — disable TypeScript declaration generation.
      // Note: `typescript` must still be installed as a devDep because
      // @module-federation/dts-plugin unconditionally `import`s it at
      // module load (the dts: false flag only disables the feature,
      // not the import).
      dts: false,
      // Plugin remotes are registered dynamically at runtime from the
      // backend manifest (see src/utils/federation.js).
      exposes: {
        './stores': './src/stores/index.js',
        './repository': './src/api/repository.js',
        './MenuItems': './src/components/tools/MenuItems.vue',
        './ConfirmDialog': './src/components/tools/ConfirmDialog.vue',
      },
      // Pinned majors for version-skew protection. @module-federation/vite
      // negotiates these correctly across host and plugin even when the
      // installed minor versions differ.
      shared: {
        vue: { singleton: true, requiredVersion: '^3.4.0' },
        'vue-router': { singleton: true, requiredVersion: '^4.0.0' },
        pinia: { singleton: true, requiredVersion: '^3.0.0' },
        vuetify: { singleton: true, requiredVersion: '^4.0.0' },
        'vue3-gettext': { singleton: true, requiredVersion: '^4.0.0-beta.1' },
      },
    }),
    relocateMfBootstrap(),
  ],
  base: '/',
  define: { 'process.env': {} },
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
  preview: {
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
    target: 'esnext',
    modulePreload: false,
    minify: false,
    cssCodeSplit: false,
  },
})
