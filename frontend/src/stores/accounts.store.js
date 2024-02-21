import { defineStore } from 'pinia'
import { ref } from 'vue'

import { useBusStore } from './bus.store'

import accountsApi from '@/api/accounts'
import gettext from '@/plugins/gettext'

export const useAccountsStore = defineStore('accounts', () => {
  const busStore = useBusStore()

  const { $gettext } = gettext

  const accounts = ref({})
  const accountsLoaded = ref(false)

  async function $reset() {
    accounts.value = {}
    accountsLoaded.value = false
  }

  async function getAll() {
    accounts.value = {}
    return accountsApi.getAll().then((response) => {
      for (const account of response.data) {
        accounts.value[account.pk] = account
      }
      return response
    })
  }

  async function getAccount(pk) {
    accountsLoaded.value = false
    return accountsApi
      .get(pk)
      .then((response) => {
        accounts.value[pk] = response.data
        return response
      })
      .finally(() => {
        accountsLoaded.value = true
      })
  }

  async function updateAccount(data) {
    return accountsApi.patch(data.pk, data).then((response) => {
      accounts.value[data.pk] = response.data
      busStore.displayNotification({ msg: $gettext('Account updated') })
      return response
    })
  }

  async function createAccount(data) {
    return accountsApi.create(data).then((response) => {
      accounts.value[response.data.pk] = response.data
      busStore.displayNotification({ msg: $gettext('Account created') })
      return response
    })
  }

  async function deleteAccount(pk, options) {
    accountsLoaded.value = false
    return accountsApi
      .delete(pk, options)
      .then((response) => {
        busStore.displayNotification({
          msg: $gettext('Account successfully deleted'),
        })
        return response
      })
      .finally(() => (accountsLoaded.value = true))
  }
  return {
    accounts,
    accountsLoaded,
    getAll,
    getAccount,
    updateAccount,
    createAccount,
    deleteAccount,
    $reset,
  }
})
