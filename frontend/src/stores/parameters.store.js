import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useParametersStore = defineStore('parameters', () => {
  const imapMigrationEnabled = ref(null)

  async function $reset() {
    imapMigrationEnabled.value = null
  }

  return { imapMigrationEnabled, $reset }
})
