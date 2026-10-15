import { defineStore } from 'pinia'
import { ref } from 'vue'

import domainApi from '@/api/domains'

export const useDomainsStore = defineStore('domains', () => {
  const domainsLoaded = ref(false)
  const domains = ref([])

  async function $reset() {
    domainsLoaded.value = false
    domains.value = []
  }

  async function getDomains() {
    domainsLoaded.value = false
    domains.value = await domainApi.getAllDomains()
    domainsLoaded.value = true
  }

  function getDomainName(domainId) {
    if (typeof domainId === 'object') {
      return domainId.name
    }
    return domains.value.find((domain) => domain.pk === domainId).name
  }

  return {
    domainsLoaded,
    domains,
    getDomainName,
    getDomains,
    $reset,
  }
})
