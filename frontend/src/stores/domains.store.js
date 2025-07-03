import { defineStore } from 'pinia'
import { ref } from 'vue'

import domainApi from '@/api/domains'

export const useDomainsStore = defineStore('domains', () => {
  const domainsLoaded = ref(false)
  const domains = ref([])

  async function $reset() {
    domainsLoaded.value = false
    domains.value = {}
  }

  async function getDomains() {
    domainsLoaded.value = false
    try {
      const resp = await domainApi.getDomains()
      domains.value = resp.data
    } finally {
      domainsLoaded.value = false
    }
  }

  return {
    domainsLoaded,
    domains,
    getDomains,
    $reset,
  }
})
