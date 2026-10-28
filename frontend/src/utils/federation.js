import { createInstance } from '@module-federation/runtime'
import gettext from '@/plugins/gettext'

// @module-federation/vite skips auto-init for "providers only" (no remotes
// in vite.config), but we register remotes dynamically at runtime, so we
// need an initialized instance. createInstance is the v2 replacement for
// the deprecated init() entry point.
const instance = createInstance({
  name: 'modoboa_host',
  remotes: [],
})

const registeredRemotes = new Set()
// remote name -> exposed translations module ("./translations"), then the
// promise of its loading once requested
const remoteTranslations = new Map()

function toRemotePath(remoteName, modulePath) {
  // modulePath is "./Component" — convert to "remoteName/Component".
  return modulePath.startsWith('./')
    ? `${remoteName}/${modulePath.slice(2)}`
    : `${remoteName}/${modulePath}`
}

function mergeTranslations(pluginTranslations) {
  const merged = { ...gettext.translations }
  for (const [lang, messages] of Object.entries(pluginTranslations || {})) {
    // Core messages win so a plugin can't alter host strings
    merged[lang] = { ...messages, ...merged[lang] }
  }
  gettext.translations = merged
}

function loadTranslations(remoteName) {
  const entry = remoteTranslations.get(remoteName)
  if (typeof entry !== 'string') {
    return entry
  }
  const promise = instance
    .loadRemote(toRemotePath(remoteName, entry))
    .then((mod) =>
      mergeTranslations(mod && 'default' in mod ? mod.default : mod)
    )
    .catch((err) =>
      console.error(`Failed to load translations of ${remoteName}`, err)
    )
  remoteTranslations.set(remoteName, promise)
  return promise
}

export function registerRemote(remote) {
  if (!remote || !remote.name || !remote.url) {
    return false
  }
  if (registeredRemotes.has(remote.name)) {
    return true
  }
  instance.registerRemotes([
    {
      name: remote.name,
      entry: remote.url,
      type: remote.format || 'module',
    },
  ])
  registeredRemotes.add(remote.name)
  if (remote.translations) {
    remoteTranslations.set(remote.name, remote.translations)
  }
  return true
}

export function loadRemoteComponent(remoteName, modulePath) {
  const path = toRemotePath(remoteName, modulePath)
  // Translations must be merged before the component renders its strings
  return () =>
    Promise.resolve(loadTranslations(remoteName))
      .then(() => instance.loadRemote(path))
      .then((mod) => (mod && 'default' in mod ? mod.default : mod))
}

export { instance }
