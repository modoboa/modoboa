<template>
  <v-app>
    <slot name="navbar">
      <NavBar :color="color" :menu-items="menuItems" />
    </slot>
    <slot name="topbar">
      <TopMenu :user="authUser" />
    </slot>
    <!-- At the bottom: the top menu is fixed in the top right corner -->
    <v-footer
      v-if="theme?.theme_banner_message"
      app
      color="secondary"
      class="justify-center text-body-2"
    >
      {{ theme.theme_banner_message }}
      <a
        v-if="theme.theme_banner_link_url"
        :href="theme.theme_banner_link_url"
        target="_blank"
        rel="noopener"
        class="ml-2 font-weight-bold text-decoration-underline banner-link"
      >
        {{ theme.theme_banner_link_label || theme.theme_banner_link_url }}
      </a>
    </v-footer>
    <ConnectedView>
      <template v-if="$slots.header" #header>
        <slot name="header" />
      </template>
    </ConnectedView>
    <v-snackbar
      v-model="snackbar"
      :color="notificationColor"
      :timeout="notificationTimeout"
      :timer="!!notificationAction"
      location="top"
    >
      {{ notification }}
      <template #actions>
        <v-btn
          v-if="notificationAction"
          color="white"
          variant="text"
          @click="runNotificationAction"
        >
          {{ notificationAction.text }}
        </v-btn>
        <v-btn color="white" variant="text" @click="snackbar = false">
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
const { theme, enableTheme } = useModoboaTheme()

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
const notificationTimeout = computed(() => busStore.notificationTimeout)
const notification = computed(() => busStore.notification)
const notificationAction = computed(() => busStore.notificationAction)
const snackbar = ref(false)

const runNotificationAction = () => {
  snackbar.value = false
  notificationAction.value.callback()
}

busStore.$onAction(({ name, after }) => {
  if (name === 'displayNotification') {
    after(() => {
      snackbar.value = true
    })
  }
  if (name === 'hideNotification') {
    after(() => {
      snackbar.value = false
    })
  }
}, true)

if (props.loadTheme) {
  await enableTheme()
}
</script>

<style scoped>
.banner-link {
  color: inherit;
}
</style>
