import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebmailStore = defineStore('webmail', () => {
  const selection = ref([])
  const listingKey = ref(0)

  return {
    selection,
    listingKey,
  }
})
