import { createInstance } from '@module-federation/runtime'

// @module-federation/vite skips auto-init for "providers only" (no remotes
// in vite.config), but we register remotes dynamically at runtime, so we
// need an initialized instance. createInstance is the v2 replacement for
// the deprecated init() entry point.
const instance = createInstance({
  name: 'modoboa_host',
  remotes: [],
})

const registeredRemotes = new Set()

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
  return true
}

export function loadRemoteComponent(remoteName, modulePath) {
  // modulePath is "./Component" — convert to "remoteName/Component".
  const path = modulePath.startsWith('./')
    ? `${remoteName}/${modulePath.slice(2)}`
    : `${remoteName}/${modulePath}`
  return () =>
    instance
      .loadRemote(path)
      .then((mod) => (mod && 'default' in mod ? mod.default : mod))
}

export { instance }
