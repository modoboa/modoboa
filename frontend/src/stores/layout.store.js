import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useLayoutStore = defineStore('layout', () => {
  const leftMenuItems = ref([])
  const compactLeftMenu = ref(false)

  function setLeftMenuItems(items) {
    leftMenuItems.value = items
  }

  async function $reset() {
    leftMenuItems.value = []
    compactLeftMenu.value = false
  }

  return {
    leftMenuItems,
    compactLeftMenu,
    setLeftMenuItems,
    $reset,
  }
})
