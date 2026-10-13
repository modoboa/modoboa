// Simple bus to handle global events like sending notifications to the user
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useBusStore = defineStore('bus', () => {
  const notification = ref('')
  const notificationColor = ref('')
  // In ms, -1 to keep the notification displayed
  const notificationTimeout = ref(5000)
  // Button displayed along the notification: { text, callback }
  const notificationAction = ref(null)
  const dataKey = ref(1)
  const mbCounterKey = ref(1)

  async function $reset() {
    notification.value = ''
    notificationColor.value = ''
    notificationTimeout.value = 5000
    notificationAction.value = null
    dataKey.value = 1
    mbCounterKey.value = 1
  }

  function displayNotification(options) {
    notification.value = options.msg
    notificationColor.value = options.type ? options.type : 'success'
    // Not kept for the next notifications
    notificationTimeout.value = options.timeout ?? 5000
    notificationAction.value = options.action || null
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
    notificationTimeout,
    notificationAction,
    displayNotification,
    hideNotification,
    reloadMailboxCounters,
    dataKey,
    mbCounterKey,
    reloadData,
    $reset,
  }
})
