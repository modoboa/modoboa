import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebmailStore = defineStore('webmail', () => {
  const selection = ref([])
  const listingKey = ref(0)

  const $reset = async () => {
    selection.value = []
    listingKey.value = 0
  }

  return {
    selection,
    listingKey,
    $reset,
  }
})
