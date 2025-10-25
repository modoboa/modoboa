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
      const resp = await domainApi.getDomains({ page_size: 0 })
      domains.value = resp.data.results
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
