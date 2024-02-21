// Simple bus to handle global events like sending notifications to the user
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useBusStore = defineStore('bus', () => {
  const notification = ref({})
  const notificationColor = ref('')

  function displayNotification(options) {
    notification.value = options.msg
    notificationColor.value = options.type ? options.type : 'success'
  }
  return {
    notification,
    notificationColor,
    displayNotification,
  }
})
