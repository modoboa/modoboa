<template>
  <v-app>
    <slot name="navbar">
      <NavBar :color="color" :menu-items="menuItems" />
    </slot>
    <slot name="topbar">
      <TopMenu :user="authUser" />
    </slot>
    <ConnectedView />
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
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import { useModoboaTheme } from '@/composables/theme'
import ConnectedView from './ConnectedView.vue'
import NavBar from '@/components/shared/NavBar.vue'
import TopMenu from '@/components/shared/TopMenu.vue'

const authStore = useAuthStore()
const busStore = useBusStore()
const { $gettext } = useGettext()
const { enableTheme } = useModoboaTheme()

const props = defineProps({
  color: {
    type: String,
    default: 'primary',
  },
  menuItems: {
    type: Array,
    default: null,
  },
  loadTheme: {
    type: Boolean,
    default: true,
  },
})

const authUser = computed(() => authStore.authUser)
const notificationColor = computed(() => busStore.notificationColor)
const notification = computed(() => busStore.notification)
const snackbar = ref(false)

const notificationTimeout = 2000

busStore.$onAction(({ name, after }) => {
  if (name === 'displayNotification') {
    after(() => {
      snackbar.value = true
    })
  }
}, true)

if (props.loadTheme) {
  await enableTheme()
}
</script>

<style>
.v-application {
  background-color: #f7f8fa !important;
}
</style>
