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
import { useTheme } from 'vuetify'
import { useAuthStore, useBusStore } from '@/stores'
import ConnectedView from './ConnectedView.vue'
import NavBar from '@/components/shared/NavBar.vue'
import TopMenu from '@/components/shared/TopMenu.vue'
import themeApi from '@/api/theme'

const authStore = useAuthStore()
const busStore = useBusStore()
const { $gettext } = useGettext()
const theme = useTheme()

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
  themeApi.getTheme().then((response) => {
    if (
      response.data.theme_primary_color !==
      theme.themes.value.light.colors.primary
    ) {
      theme.themes.value.light.colors.primary =
        response.data.theme_primary_color
    }
    if (
      response.data.theme_primary_color_light !==
      theme.themes.value.light.colors['primary-lighten-1']
    ) {
      theme.themes.value.light.colors['primary-lighten-1'] =
        response.data.theme_primary_color_light
    }
    if (
      response.data.theme_primary_color_dark !==
      theme.themes.value.light.colors['primary-darken-1']
    ) {
      theme.themes.value.light.colors['primary-darken-1'] =
        response.data.theme_primary_color_dark
    }
    if (
      response.data.theme_secondary_color !==
      theme.themes.value.light.colors.secondary
    ) {
      theme.themes.value.light.colors.secondary =
        response.data.theme_secondary_color
    }
    if (
      response.data.theme_label_color !== theme.themes.value.light.colors.label
    ) {
      theme.themes.value.light.colors.label = response.data.theme_label_color
    }
  })
}
</script>

<style>
.v-application {
  background-color: #f7f8fa !important;
}
</style>
