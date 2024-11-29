<template>
  <v-navigation-drawer
    v-model="drawer"
    :rail="rail"
    permanent
    :color="mainColor"
    app
  >
    <div class="d-flex align-center">
      <v-img
        src="@/assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="190"
        class="logo"
        @click="router.push({ name: 'Dashboard' })"
      />
      <v-btn
        :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
        variant="text"
        @click.stop="rail = !rail"
      >
      </v-btn>
    </div>

    <v-list nav>
      <template v-for="item in menuItems" :key="item.text">
        <template v-if="displayMenuItem(item)">
          <v-list-item
            v-if="!item.children"
            :value="item"
            :to="item.to"
            link
            :exact="item.exact"
            :title="item.text"
            :prepend-icon="item.icon"
          >
            <template v-if="item.withBell && displayInformationBell" #append>
              <v-icon color="red" icon="mdi-bell-alert-outline" />
            </template>
          </v-list-item>
          <v-list-group v-else :value="item.text">
            <template #activator="{ props }">
              <v-list-item
                v-bind="props"
                :key="item.text"
                :title="item.text"
                color="white"
                :prepend-icon="item.icon"
              >
              </v-list-item>
            </template>
            <template v-for="subitem in item.children" :key="subitem.text">
              <v-list-item
                v-if="displayMenuItem(subitem)"
                :to="subitem.to"
                link
                :title="subitem.text"
                :value="subitem"
              ></v-list-item>
            </template>
          </v-list-group>
        </template>
      </template>
    </v-list>
    <template #append>
      <v-menu v-if="isAuthenticated" rounded="lg" offset-y top>
        <template #activator="{ props }">
          <div
            :class="[
              backgroundColor,
              'd-flex',
              'justify-center',
              'align-center',
              'pa-2',
            ]"
          >
            <v-btn
              v-bind="props"
              :class="[backgroundColor, 'text-white']"
              rounded
              density="compact"
              height="48"
              elevation="0"
            >
              <v-avatar size="40" color="primary">
                <span class="text-white headline">{{ userInitials }}</span>
              </v-avatar>
              <template v-if="!rail">
                <span class="mx-2">{{ displayName }}</span>
                <v-icon class="float-right">mdi-chevron-up</v-icon>
              </template>
            </v-btn>
          </div>
        </template>
        <v-list>
          <v-list-item
            v-for="item in userMenuItems"
            :key="item.text"
            :to="item.to"
            link
            @click="item.click"
          >
            <template #prepend>
              <v-icon :icon="item.icon"></v-icon>
            </template>
            <v-list-item-title>{{ item.text }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-navigation-drawer>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'
import { getActivePinia } from 'pinia'
import { useGlobalStore, useAuthStore, useParametersStore } from '@/stores'
import parametersApi from '@/api/parameters'

const globalStore = useGlobalStore()
const authStore = useAuthStore()
const parametersStore = useParametersStore()
const route = useRoute()
const router = useRouter()
const { $gettext } = useGettext()

const rail = ref(false)
const drawer = ref(true)

const authUser = computed(() => authStore.authUser)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const backgroundColor = computed(() =>
  route.meta.layout === 'account' ? 'bg-grey-darken-1' : 'bg-primary-darken-1'
)
const userInitials = computed(() => {
  let initials = null
  if (authUser.value.first_name) {
    initials = authUser.value.first_name[0]
  }
  if (authUser.value.last_name) {
    initials = initials
      ? initials + authUser.value.last_name[0]
      : authUser.value.last_name[0]
  }
  if (!initials) {
    initials = authUser.value.username[0]
  }
  return initials
})
const displayName = computed(() => {
  return authUser.value.first_name || authUser.value.last_name
    ? `${authUser.value.first_name} ${authUser.value.last_name}`
    : authUser.value.username
})

const menuItems = computed(() => {
  if (route.meta.layout === 'account') {
    return getUserSettingsMenuItems()
  }
  return mainMenuItems
})

const mainColor = computed(() => {
  if (route.meta.layout === 'account') {
    return 'grey'
  }
  return 'primary'
})

const imapMigration = computed(() => parametersStore.imapMigrationEnabled)

const displayInformationBell = computed(
  () =>
    globalStore.notifications.length !== undefined &&
    globalStore.notifications.length !== 0
)

const settings = []
const mainMenuItems = [
  {
    text: $gettext('Dashboard'),
    to: { name: 'Dashboard' },
    exact: true,
    icon: 'mdi-view-dashboard-outline',
  },
  {
    text: $gettext('Domains'),
    to: { name: 'DomainList' },
    icon: 'mdi-domain',
    roles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
  },
  {
    text: $gettext('Identities'),
    to: { name: 'Identities' },
    icon: 'mdi-account',
    roles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
  },
  {
    text: $gettext('Alarms'),
    to: { name: 'Alarms' },
    icon: 'mdi-bell',
  },
  {
    icon: 'mdi-history',
    text: $gettext('Monitoring'),
    roles: ['SuperAdmins', 'Resellers', 'DomainAdmins'],
    children: [
      {
        text: $gettext('Statistics'),
        to: { name: 'Statistics' },
        roles: ['SuperAdmins'],
      },
      {
        text: $gettext('Audit trail'),
        to: { name: 'AuditTrail' },
        roles: ['SuperAdmins'],
      },
      {
        text: $gettext('Messages'),
        to: { name: 'MessageLog' },
        roles: ['DomainAdmins', 'Resellers', 'SuperAdmins'],
      },
    ],
  },
  {
    icon: 'mdi-email-sync-outline',
    text: $gettext('IMAP Migration'),
    roles: ['SuperAdmins', 'Resellers'],
    children: [
      {
        text: $gettext('Email providers'),
        to: { name: 'ProvidersList' },
        roles: ['SuperAdmins', 'Resellers'],
      },
      {
        text: $gettext('Migrations'),
        to: { name: 'MigrationsList' },
        roles: ['Resellers', 'SuperAdmins'],
      },
    ],
  },
  {
    icon: 'mdi-cog',
    text: $gettext('Settings'),
    children: settings,
    roles: ['SuperAdmins'],
  },
  {
    icon: 'mdi-information',
    text: $gettext('Information'),
    roles: ['SuperAdmins'],
    to: { name: 'Information' },
    withBell: true,
  },
]

const userMenuItems = [
  {
    text: $gettext('Account'),
    icon: 'mdi-account-circle-outline',
    to: { name: 'AccountSettings' },
    click: () => null,
  },
  {
    text: $gettext('Logout'),
    icon: 'mdi-logout',
    click: logout,
  },
]

if (isAuthenticated.value && authUser.value.role !== 'SimpleUsers') {
  userMenuItems.unshift({
    text: $gettext('Admin'),
    to: { name: 'Dashboard' },
    icon: 'mdi-view-dashboard-outline',
  })
}

function getUserSettingsMenuItems() {
  const result = []

  if (authUser.value.mailbox) {
    result.push({
      text: $gettext('Filters'),
      to: { name: 'AccountFilters' },
      icon: 'mdi-filter',
    })
  }
  result.push({
    text: $gettext('Settings'),
    to: { name: 'AccountSettings' },
    icon: 'mdi-cog',
  })
  return result
}

function displayMenuItem(item) {
  if (isAuthenticated.value) {
    const condition =
      (item.roles === undefined ||
        item.roles.indexOf(authUser.value.role) !== -1) &&
      (item.condition === undefined || item.condition()) &&
      item.activated !== false
    if (item.icon === 'mdi-email-sync-outline') {
      // For imapMigration
      return condition && imapMigration.value
    }
    return condition
  }
}

async function logout() {
  getActivePinia()._s.forEach(async (store) => await store.$reset())
}

onMounted(() => {
  if (authUser.value.role === 'SuperAdmins') {
    parametersApi.getApplications().then((response) => {
      response.data.forEach((item) => {
        settings.push({
          text: item.label,
          to: { name: 'ParametersEdit', params: { app: item.name } },
        })
      })
    })
    globalStore.fetchNotifications()
    if (parametersStore.imapMigrationEnabled === null) {
      parametersApi.getApplication('imap_migration').then((response) => {
        parametersStore.imapMigrationEnabled =
          response.data.params.enabled_imapmigration
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.v-list-item {
  &--active {
    &::before {
      opacity: 0;
    }
    background-color: #034bad !important;
    color: white;
    opacity: 1;
  }
}

.logo {
  cursor: pointer;
}
</style>
