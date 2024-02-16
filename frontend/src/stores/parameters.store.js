import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useParametersStore = defineStore('parameters', () => {
  const imapMigrationEnabled = ref(null)

  return { imapMigrationEnabled }
})
