import { defineStore } from 'pinia'
import { ref } from 'vue'
import aliasesApi from '@/api/aliases'
import { useBusStore } from './bus.store'

import gettext from '@/plugins/gettext'

export const useAliasesStore = defineStore('aliases', () => {
  const busStore = useBusStore()
  const { $gettext } = gettext

  const aliases = ref({})
  const aliasesLoaded = ref(false)

  async function $reset() {
    aliases.value = {}
    aliasesLoaded.value = false
  }

  async function getAll() {
    aliasesLoaded.value = false
    return aliasesApi
      .getAll()
      .then((response) => {
        aliases.value = {}
        for (const account of response.data) {
          aliases.value[account.pk] = account
        }
        return response
      })
      .finally(() => (aliasesLoaded.value = true))
  }

  async function getAlias(pk) {
    aliasesLoaded.value = false
    return aliasesApi
      .get(pk)
      .then((response) => {
        aliases.value[pk] = response.data
        return response
      })
      .finally(() => (aliasesLoaded.value = true))
  }

  async function createAlias(data) {
    aliasesLoaded.value = false
    return aliasesApi
      .create(data)
      .then((response) => {
        aliases.value[response.data.pk] = response.data
        busStore.displayNotification({
          msg: $gettext('Alias successfully created'),
        })
        return response
      })
      .finally(() => (aliasesLoaded.value = true))
  }

  async function deleteAlias(pk) {
    aliasesLoaded.value = false
    return aliasesApi
      .delete(pk)
      .then((response) => {
        busStore.displayNotification({
          msg: $gettext('Alias successfully deleted'),
        })
        return response
      })
      .finally(() => (aliasesLoaded.value = true))
  }

  async function updateAlias(data) {
    aliasesLoaded.value = false
    return aliasesApi
      .patch(data.pk, data)
      .then((response) => {
        aliases.value[data.pk] = response.data
        busStore.displayNotification({ msg: $gettext('Alias updated') })
        return response
      })
      .finally(() => (aliasesLoaded.value = true))
  }

  return {
    aliases,
    aliasesLoaded,
    getAll,
    getAlias,
    createAlias,
    deleteAlias,
    updateAlias,
    $reset,
  }
})
