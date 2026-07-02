/**
 * main.js
 *
 * Loads the runtime config, then either redirects an unauthenticated visitor
 * straight to the OIDC login (without booting the heavy SPA) or mounts the app.
 */

// Composables
import { createApp } from 'vue'

// api
import repository from '@/api/repository.js'

import { setGlobalConfig } from '@/config'
import { createUserManager } from '@/oidc'

// Force @/auth-gate to be emitted as its own chunk so the inline login gate in
// index.html can load it (to redirect an unauthenticated visitor) without
// booting the SPA. This branch never runs — it exists only so the bundler
// keeps the chunk.
if (window.__forceAuthGateChunk__) {
  import('@/auth-gate')
}

// Dev-only: intercept the API with mock data so the UI can run with no backend.
// Gated by VITE_MOCK_API — the dynamic import is dead-code-eliminated in
// production builds (where the flag is unset), so msw never ships.
async function startMockApi() {
  if (!import.meta.env.VITE_MOCK_API) {
    return
  }
  if (
    window.location.protocol === 'https:' &&
    ['localhost', '127.0.0.1'].includes(window.location.hostname)
  ) {
    window.location.replace(
      `${window.location.href.replace(/^https:/, 'http:')}`
    )
    return
  }
  // Expose the mock flag as a runtime global: import.meta.env replacement is
  // not reliably injected into the Module-Federation-exposed modules (e.g.
  // the stores), so consumers there read this global instead.
  globalThis.__MODOBOA_MOCK_API__ = true
  if (window.__mswStarted) {
    return
  }
  window.__mswStarted = true
  const { worker } = await import('@/mocks/browser')
  await worker.start({ onUnhandledRequest: 'bypass' })
}

function inMockMode() {
  return Boolean(
    import.meta.env.VITE_MOCK_API || globalThis.__MODOBOA_MOCK_API__
  )
}

/**
 * For an unauthenticated visitor, redirect to the OIDC login *before* the app
 * boots, so the login page appears sooner. Returns true when it redirected
 * (the caller must then not mount). Defensive: any failure (or the OIDC
 * callback / login routes, or mock mode) falls through to a normal mount, so
 * the worst case is exactly today's behaviour.
 */
async function redirectToLoginIfNeeded(config) {
  if (inMockMode()) {
    return false
  }
  // The OIDC callback (and the login routes) must be handled by the app.
  if (window.location.pathname.startsWith('/login')) {
    return false
  }
  try {
    const manager = createUserManager(config)
    const user = await manager.getUser()
    if (user && !user.expired) {
      return false
    }
    await manager.signinRedirect()
    return true
  } catch (error) {
    console.warn('Early auth check failed; booting the app normally.', error)
    return false
  }
}

async function mountApp(config) {
  // Loaded dynamically so an unauthenticated visitor (redirected above) never
  // downloads the app shell / Vuetify chunks.
  const [{ default: App }, { registerPlugins }] = await Promise.all([
    import('./App.vue'),
    import('@/plugins'),
  ])
  const app = createApp(App)
  registerPlugins(app)
  app.mount('#app')
  app.provide('$config', config)
}

async function boot() {
  await startMockApi()

  const response = await fetch(import.meta.env.BASE_URL + 'config.json')
  const config = await response.json()
  if (!config.API_BASE_URL) {
    throw new Error('API_BASE_URL is not defined in config.json')
  }
  setGlobalConfig(config)
  repository.defaults.baseURL = config.API_BASE_URL

  if (await redirectToLoginIfNeeded(config)) {
    return
  }
  await mountApp(config)
}

boot().catch((error) => {
  console.error('Failed to start the application:', error)
})
