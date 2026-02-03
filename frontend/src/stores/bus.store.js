// Simple bus to handle global events like sending notifications to the user
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useBusStore = defineStore('bus', () => {
  const notification = ref('')
  const notificationColor = ref('')
  const notificationTimeout = ref(2000)
  const dataKey = ref(1)
  const mbCounterKey = ref(1)

  async function $reset() {
    notification.value = ''
    notificationColor.value = ''
    notificationTimeout.value = 2000
    dataKey.value = 1
    mbCounterKey.value = 1
  }

  function displayNotification(options) {
    notification.value = options.msg
    notificationColor.value = options.type ? options.type : 'success'
    if (options.timeout !== undefined) {
      notificationTimeout.value = options.timeout
    }
  }

  function hideNotification() {
    notification.value = ''
  }

  function reloadData() {
    dataKey.value++
  }

  function reloadMailboxCounters() {
    mbCounterKey.value++
  }

  return {
    notification,
    notificationColor,
    displayNotification,
    hideNotification,
    reloadMailboxCounters,
    dataKey,
    mbCounterKey,
    reloadData,
    $reset,
  }
})
