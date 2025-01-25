import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useLayoutStore = defineStore('layout', () => {
  const leftMenuItems = ref([])

  function setLeftMenuItems(items) {
    leftMenuItems.value = items
  }

  async function $reset() {
    leftMenuItems.value = []
  }

  return {
    leftMenuItems,
    setLeftMenuItems,
    $reset,
  }
})
