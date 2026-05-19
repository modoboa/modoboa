import { computed, defineAsyncComponent, ref } from 'vue'
import { defineStore } from 'pinia'
import pluginsApi from '@/api/plugins'
import { loadRemoteComponent } from '@/utils/federation'

export const usePluginsStore = defineStore('plugins', () => {
  const manifests = ref([])
  const loaded = ref(false)

  async function fetchManifests({ force = false } = {}) {
    if (loaded.value && !force) {
      return manifests.value
    }
    const response = await pluginsApi.getManifests()
    manifests.value = response.data
    loaded.value = true
    return manifests.value
  }

  const routes = computed(() =>
    manifests.value.flatMap((manifest) => manifest.routes || [])
  )

  function toMenuItem(entry) {
    const item = {
      text: entry.label,
      icon: entry.icon || undefined,
      roles: entry.roles && entry.roles.length ? entry.roles : undefined,
    }
    if (entry.to) {
      item.to = { name: entry.to }
    } else if (entry.url) {
      item.to = entry.url
    }
    if (Array.isArray(entry.children) && entry.children.length) {
      item.children = entry.children.map(toMenuItem)
    }
    return item
  }

  function menuEntriesByCategory(category) {
    return manifests.value.flatMap((manifest) =>
      (manifest.menu_entries || []).filter(
        (entry) => (entry.category || 'admin') === category
      )
    )
  }

  function menuItemsByCategory(category) {
    return menuEntriesByCategory(category).map(toMenuItem)
  }

  function wrapExtensionItem(item, remote) {
    const wrapped = { ...item, source: remote?.name }
    if (typeof item.component === 'string' && remote?.name) {
      wrapped.component = defineAsyncComponent(
        loadRemoteComponent(remote.name, item.component)
      )
    }
    if (item.summary && typeof item.summary === 'object') {
      const summary = { ...item.summary }
      if (typeof summary.component === 'string' && remote?.name) {
        summary.component = defineAsyncComponent(
          loadRemoteComponent(remote.name, summary.component)
        )
      }
      wrapped.summary = summary
    }
    return wrapped
  }

  function uiExtensions(extensionPointId) {
    return manifests.value.flatMap((manifest) => {
      const items = manifest.ui_extensions?.[extensionPointId] || []
      return items.map((item) => wrapExtensionItem(item, manifest.remote))
    })
  }

  function $reset() {
    manifests.value = []
    loaded.value = false
  }

  return {
    manifests,
    loaded,
    routes,
    fetchManifests,
    menuEntriesByCategory,
    menuItemsByCategory,
    uiExtensions,
    $reset,
  }
})
