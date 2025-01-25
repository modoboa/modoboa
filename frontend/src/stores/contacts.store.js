import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useContactsStore = defineStore('contacts', () => {
  const currentCategory = ref(null)

  function setCurrentCategory(category) {
    currentCategory.value = category
  }

  async function $reset() {
    currentCategory.value = null
  }

  return {
    currentCategory,
    setCurrentCategory,
    $reset,
  }
})
