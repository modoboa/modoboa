import { defineStore } from 'pinia'
import { ref } from 'vue'

import { useAccountsStore } from './accounts.store'
import { useAliasesStore } from './aliases.store'

import identitiesApi from '@/api/identities'

import gettext from '@/plugins/gettext'

export const useIdentitiesStore = defineStore('identities', () => {
  const aliasesStore = useAliasesStore()
  const accountsStore = useAccountsStore()

  const { $gettext } = gettext

  const identitiesLoaded = ref(false)
  const identities = ref([])

  async function $reset() {
    identitiesLoaded.value = false
    identities.value = []
  }

  async function _getIndexByPk(type, pk) {
    for (let i = 0; i < identities.value.length; i++) {
      if (identities.value[i].pk === pk && identities.value[i].type === type) {
        return i
      }
    }
  }

  async function _deleteIdByPkAndType(type, pk) {
    _getIndexByPk(type, pk).then((index) => {
      if (index !== null) {
        identities.value.splice(index, 1)
      }
    })
  }

  async function getIdentities() {
    identitiesLoaded.value = false
    return identitiesApi.getAll().then((response) => {
      identities.value = response.data
      identitiesLoaded.value = true
      return response
    })
  }

  async function _accountToId(data, update = false) {
    const account = data
    let indexSearcher = null
    if (update) {
      indexSearcher = _getIndexByPk('account', data.pk)
    }
    let name_or_rcpt = '---'
    if (account.first_name !== '') {
      name_or_rcpt = account.first_name
    }
    if (account.last_name !== '') {
      name_or_rcpt =
        name_or_rcpt === ''
          ? account.last_name
          : `${name_or_rcpt} ${account.last_name}`
    }
    const newIdentity = {
      pk: account.pk,
      type: account.type,
      identity: account.username,
      name_or_rcpt: name_or_rcpt,
      tags: [
        { name: 'account', label: $gettext('account'), type: 'idt' },
        {
          name: account.role,
          label: $gettext(account.role),
          type: 'grp',
        },
      ],
      possible_actions: [],
    }

    if (update) {
      indexSearcher.then((index) => {
        identities.value[index] = newIdentity
        return
      })
    }
    identities.value.push(newIdentity)
  }

  async function _aliasToId(data, update = false) {
    let indexSearcher = null
    const alias = data
    if (update) {
      indexSearcher = _getIndexByPk('alias', data.pk)
    }
    const name_or_rcpt =
      alias.recipients.length > 1
        ? `${alias.recipients[0]}, ...`
        : alias.recipients[0]
    const newIdentity = {
      pk: alias.pk,
      type: alias.type,
      identity: alias.address,
      name_or_rcpt: name_or_rcpt,
      tags: [{ name: 'alias', label: $gettext('alias'), type: 'idt' }],
      possible_actions: [],
    }
    if (update) {
      indexSearcher.then((index) => {
        identities.value[index] = newIdentity
        return
      })
    }
    identities.value.push(newIdentity)
  }

  async function createIdentity(type, data) {
    identitiesLoaded.value = false
    if (type === 'alias') {
      return aliasesStore.createAlias(data).then((response) => {
        _aliasToId(response.data)
        identitiesLoaded.value = true
        return response
      })
    } else if (type === 'account') {
      return accountsStore.createAccount(data).then((response) => {
        _accountToId(response.data)
        identitiesLoaded.value = true
        return response
      })
    }
  }

  async function updateIdentity(type, data) {
    identitiesLoaded.value = false
    if (type === 'alias') {
      return aliasesStore
        .updateAlias(data)
        .then((response) => {
          _aliasToId(response.data, true)
          return response
        })
        .finally(() => (identitiesLoaded.value = true))
    } else if (type === 'account') {
      return accountsStore
        .updateAccount(data)
        .then((response) => {
          _accountToId(response.data, true)
          return response
        })
        .finally(() => (identitiesLoaded.value = true))
    }
  }

  async function deleteIdentity(type, pk, options) {
    identitiesLoaded.value = false
    if (type === 'alias') {
      return aliasesStore.deleteAlias(pk).then((response) => {
        _deleteIdByPkAndType(type, pk)
        identitiesLoaded.value = true
        return response
      })
    } else if (type === 'account') {
      return accountsStore.deleteAccount(pk, options).then((response) => {
        _deleteIdByPkAndType(type, pk)
        identitiesLoaded.value = true
        return response
      })
    }
  }

  return {
    identities,
    getIdentities,
    identitiesLoaded,
    deleteIdentity,
    createIdentity,
    updateIdentity,
    $reset,
  }
})
