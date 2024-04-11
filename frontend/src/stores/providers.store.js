import { defineStore } from 'pinia'
import { useBusStore } from './bus.store'
import { ref } from 'vue'
import gettext from '@/plugins/gettext'

import providersApi from '@/api/imap_migration/providers'

export const useProvidersStore = defineStore('providers', () => {
  const busStore = useBusStore()
  const providersLoaded = ref(false)
  const providers = ref({})
  const { $gettext } = gettext

  async function $reset() {
    providersLoaded.value = false
    providers.value = {}
  }

  async function getProviders() {
    providers.value = {}
    providersLoaded.value = false
    return providersApi
      .getProviders()
      .then((response) => {
        for (const provider of response.data) {
          providers.value[provider.id] = provider
        }
        return response
      })
      .finally(() => (providersLoaded.value = true))
  }

  async function createProvider(data) {
    providersLoaded.value = false
    return providersApi
      .createProvider(data)
      .then((response) => {
        providers.value[response.data.id] = response.data
        return response
      })
      .finally(() => (providersLoaded.value = true))
  }

  async function deleteProvider(id) {
    providersLoaded.value = false
    return providersApi
      .deleteProvider({ id: id })
      .then((response) => {
        delete providers.value[id]
        busStore.displayNotification({
          msg: $gettext('Provider deleted'),
        })
        return response
      })
      .finally(() => (providersLoaded.value = true))
  }

  return {
    providersLoaded,
    providers,
    getProviders,
    createProvider,
    deleteProvider,
    $reset,
  }
})
