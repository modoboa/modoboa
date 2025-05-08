// Simple bus to handle global events like sending notifications to the user
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useBusStore = defineStore('bus', () => {
  const notification = ref({})
  const notificationColor = ref('')
  const dataKey = ref(1)
  const mbCounterKey = ref(1)

  async function $reset() {
    notification.value = {}
    notificationColor.value = ''
    dataKey.value = 1
    mbCounterKey.value = 1
  }

  function displayNotification(options) {
    notification.value = options.msg
    notificationColor.value = options.type ? options.type : 'success'
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
    reloadMailboxCounters,
    dataKey,
    mbCounterKey,
    $reset,
  }
})
