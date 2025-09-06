<template>
  <div v-if="user" class="top-menu">
    <v-btn
      v-if="globalStore.activeNotifications"
      icon
      color="error"
      class="mr-4"
      variant="tonal"
      size="small"
    >
      <v-icon icon="mdi-bell" />
      <v-menu activator="parent" location="bottom">
        <v-list>
          <div class="text-center">
            <v-list-item :title="$gettext('Notifications')" />
          </div>
          <v-divider></v-divider>
          <v-list-item
            v-for="notif in globalStore.notifications"
            :key="notif.id"
            :to="notif.url"
          >
            <template #prepend>
              <v-badge
                :color="notif.color"
                :content="notif.counter"
                inline
              ></v-badge>
            </template>
            <v-list-item-title>{{ notif.text }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-btn>

    <v-btn icon class="mr-4" variant="flat">
      <v-icon icon="mdi-apps" />
      <v-menu activator="parent" location="bottom">
        <v-card min-width="350" max-width="400" class="pa-4">
          <v-row class="justify-center">
            <v-col
              v-for="application in applications"
              :key="application.name"
              cols="6"
            >
              <v-sheet
                rounded
                class="application text-center pa-4 text-body-2"
                @click="$router.push(application.url)"
              >
                <v-icon
                  color="primary"
                  :icon="application.icon"
                  size="x-large"
                />
                <div class="mt-2">{{ application.label }}</div>
              </v-sheet>
            </v-col>
          </v-row>
        </v-card>
      </v-menu>
    </v-btn>

    <v-btn icon flat color="primary">
      {{ userInitials }}
      <v-menu activator="parent" location="bottom">
        <v-card min-width="300" max-width="350">
          <v-list>
            <div class="text-center">
              <v-avatar color="primary">
                <span class="text-h5">{{ userInitials }}</span>
              </v-avatar>
              <v-list-item :title="user.username" />
            </div>
            <v-divider></v-divider>
            <v-list-item
              v-for="item in userMenuItems"
              :key="item.text"
              :to="item.to"
              :href="item.href"
              link
              @click="item.click"
            >
              <template #prepend>
                <v-icon :icon="item.icon"></v-icon>
              </template>
              <v-list-item-title>{{ item.text }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-menu>
    </v-btn>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getActivePinia } from 'pinia'
import { useGettext } from 'vue3-gettext'
import { useGlobalStore } from '@/stores'
import accountApi from '@/api/account'

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  remote: {
    type: Boolean,
    default: false,
  },
})

const { $gettext } = useGettext()
const globalStore = useGlobalStore()

const applications = ref([])

const userInitials = computed(() => {
  if (props.user.first_name && props.user.last_name) {
    return `${props.user.first_name[0].toUpperCase()}${props.user.last_name[0].toUpperCase()}`
  }
  if (props.user.username) {
    return props.user.username.slice(0, 2).toUpperCase()
  }
  return ''
})

const userMenuItems = computed(() => {
  return [
    {
      text: $gettext('Account'),
      icon: 'mdi-account-circle-outline',
      to: !props.remote ? { name: 'AccountSettings' } : null,
      href: props.remote ? 'https://localhost:3000/account' : '',
      click: () => null,
    },
    {
      text: $gettext('Logout'),
      icon: 'mdi-logout',
      click: logout,
    },
  ]
})

async function logout() {
  getActivePinia()._s.forEach(async (store) => await store.$reset())
}

onMounted(() => {
  accountApi.getAvailableApplications().then((resp) => {
    applications.value = resp.data
  })
  globalStore.fetchNotifications()
})
</script>

<style scoped lang="scss">
.top-menu {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 100;
}

.application {
  cursor: pointer;
}

.application:hover {
  background-color: rgb(var(--v-theme-surface));
}
</style>
