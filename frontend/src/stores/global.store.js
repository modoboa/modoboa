import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import accountApi from '@/api/account'
import capabilitiesApi from '@/api/capabilities'
import notificationsApi from '@/api/notifications'

export const useGlobalStore = defineStore('global', () => {
  const capabilities = ref([])
  const notifications = ref([])
  const applications = ref([])

  async function fetchCapabilities() {
    const response = await capabilitiesApi.getCapabilities()
    capabilities.value = response.data.capabilities
  }
  async function fetchNotifications() {
    const response = await notificationsApi.getNotifications()
    notifications.value = response.data
  }
  async function fetchAvailableApplications() {
    if (!applications.value.length) {
      const response = await accountApi.getAvailableApplications()
      applications.value = response.data
    }
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

  const webmailEnabled = computed(
    () => applications.value.find((app) => app.name === 'webmail') !== undefined
  )

  return {
    applications,
    capabilities,
    notifications,
    fetchCapabilities,
    fetchNotifications,
    fetchAvailableApplications,
    getNotificationById,
    activeNotifications,
    adminNotifications,
    webmailEnabled,
    $reset,
  }
})
