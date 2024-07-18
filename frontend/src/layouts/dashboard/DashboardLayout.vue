<template>
  <v-app>
    <NavBar />
    <DashboardView />
    <v-snackbar
      v-model="snackbar"
      :color="notificationColor"
      :timeout="notificationTimeout"
      location="top"
    >
      {{ notification }}
      <template #actions>
        <v-btn color="white" text @click="snackbar = false">
          {{ $gettext('Close') }}
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import DashboardView from './DashboardView.vue'
import NavBar from './NavBar.vue'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'

import { useBusStore } from '@/stores'

const busStore = useBusStore()
const { $gettext } = useGettext()

const notificationColor = computed(() => busStore.notificationColor)
const notificationTimeout = 2000
const notification = computed(() => busStore.notification)
const snackbar = ref(false)

busStore.$onAction(({ name, after }) => {
  if (name === 'displayNotification') {
    after(() => {
      snackbar.value = true
    })
  }
}, true)
</script>

<style>
.v-application {
  background-color: #f7f8fa;
}
</style>
