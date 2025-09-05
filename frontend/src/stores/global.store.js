import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import capabilitiesApi from '@/api/capabilities'
import notificationsApi from '@/api/notifications'

export const useGlobalStore = defineStore('global', () => {
  const capabilities = ref([])
  const notifications = ref([])

  async function fetchCapabilities() {
    const response = await capabilitiesApi.getCapabilities()
    capabilities.value = response.data.capabilities
  }
  async function fetchNotifications() {
    const response = await notificationsApi.getNotifications()
    notifications.value = response.data
  }

  function getNotificationById(id) {
    return notifications.value.find((item) => item.id === id)
  }

  async function $reset() {
    capabilities.value = []
    notifications.value = []
  }

  const activeNotifications = computed(() => {
    return notifications.value.length !== 0
  })

  const adminNotifications = computed(() => {
    return notifications.value.filter((notif) => notif.target === 'admin')
  })

  return {
    capabilities,
    notifications,
    fetchCapabilities,
    fetchNotifications,
    getNotificationById,
    activeNotifications,
    adminNotifications,
    $reset,
  }
})
