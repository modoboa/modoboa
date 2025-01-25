import { ref } from 'vue'
import { defineStore } from 'pinia'
import adminApi from '@/api/admin'

export const useGlobalStore = defineStore('global', () => {
  const notifications = ref([])

  async function fetchNotifications() {
    const response = await adminApi.getNotifications()
    notifications.value = response.data
  }

  function getNotificationById(id) {
    return notifications.value.find((item) => item.id === id)
  }

  async function $reset() {
    notifications.value = []
  }

  return { notifications, fetchNotifications, getNotificationById, $reset }
})
