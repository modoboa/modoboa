import { defineStore } from 'pinia'
import { useBusStore } from './bus.store'
import { ref } from 'vue'
import gettext from '@/plugins/gettext'

import domainApi from '@/api/domains'

export const useDomainsStore = defineStore('domains', () => {
  const busStore = useBusStore()
  const { $gettext } = gettext
  const domainsLoaded = ref(false)
  const domains = ref({})
  const domainAliases = ref({})

  async function $reset() {
    domainsLoaded.value = false
    domains.value = {}
    domainAliases.value = {}
  }

  async function getDomains() {
    domainsLoaded.value = false
    return domainApi.getDomains().then((response) => {
      domains.value = {}
      const _domains = {}
      response.data.forEach(function (domain) {
        _domains[domain.pk] = domain
      })
      domains.value = _domains
      domainsLoaded.value = true
      return response
    })
  }

  async function getDomain(pk) {
    domainsLoaded.value = false
    return domainApi.getDomain(pk).then((response) => {
      domains.value[pk] = response.data
      domainsLoaded.value = true
      return response
    })
  }

  function getDomainByName(name) {
    for (const domain of Object.values(domains.value)) {
      if (domain.name === name) {
        return domain
      }
    }
  }

  async function createDomain(data) {
    return domainApi.createDomain(data).then((response) => {
      domains.value[response.data.pk] = response.data
      return response
    })
  }

  async function updateDomain(data) {
    return domainApi.updateDomain(data.pk, data).then((response) => {
      domains.value[data.pk] = response.data
      busStore.displayNotification({ msg: $gettext('Domain updated') })
      return response
    })
  }

  async function deleteDomain({ id, data }) {
    return domainApi.deleteDomain(id, data).then((response) => {
      delete domains.value[id]
      return response
    })
  }

  async function getAliases(name) {
    return domainApi.getDomainAliases(name).then((response) => {
      domainAliases.value[name] = response.data
      return response
    })
  }

  async function _filterAlias(domainName, pk) {
    if (domainAliases.value[domainName] !== undefined) {
      return domainAliases.value[domainName].filter((al) => al.pk != pk)
    }
  }

  async function createAlias(data) {
    return domainApi.createDomainAlias(data).then((response) => {
      busStore.displayNotification({
        msg: $gettext('Domain alias created'),
      })
      if (domains.value[data.target] != null) {
        const domain = domains.value[data.target]
        if (domainAliases.value[domain.name] !== undefined) {
          domainAliases.value[domain.name].push(response.data)
        } else {
          domainAliases.value[domain.name] = response.data
        }
        domain.domainalias_count++
      }
      return response
    })
  }

  async function deleteAlias(alias) {
    const domain = domains.value[alias.target]
    const apiRequest = domainApi.deleteDomainAlias(alias.pk)
    const filter = _filterAlias(domain.name, alias.pk)
    Promise.all([filter, apiRequest]).then((results) => {
      const newList = results[0]
      busStore.displayNotification({
        msg: $gettext('Domain alias deleted'),
      })
      if (newList != null) {
        domainAliases.value[domain.name] = newList
      }
      domain.domainalias_count--
    })
  }

  async function updateAlias(data) {
    const domain = domains.value[data.target]
    const filter = _filterAlias(domain.name, data.pk)
    const apiRequest = domainApi.updateDomainAlias(data.pk, data)
    Promise.all([filter, apiRequest]).then((results) => {
      busStore.displayNotification({
        msg: $gettext('Domain alias updated'),
      })
      const newList = results[0]
      const response = results[1]
      if (newList != null) {
        domainAliases.value[domain.name] = newList
        domainAliases.value[domain.name].push(response.data)
      } else {
        domainAliases.value[domain.name] = response.data
      }
    })
  }
  return {
    domainsLoaded,
    domains,
    domainAliases,
    getDomain,
    getDomainByName,
    getDomains,
    createDomain,
    updateDomain,
    deleteDomain,
    createAlias,
    getAliases,
    deleteAlias,
    updateAlias,
    $reset,
  }
})
