<template>
  <v-app>
    <NavBar :menu-items="menuItems" />
    <TopMenu :user="authUser" />
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore, useParametersStore } from '@/stores'
import parametersApi from '@/api/parameters'
import ConnectedView from './ConnectedView.vue'
import NavBar from '@/components/shared/NavBar.vue'
import TopMenu from '@/components/shared/TopMenu.vue'

const authStore = useAuthStore()
const busStore = useBusStore()
const parametersStore = useParametersStore()
const { $gettext } = useGettext()
const route = useRoute()

const authUser = computed(() => authStore.authUser)
const notificationColor = computed(() => busStore.notificationColor)
const notification = computed(() => busStore.notification)
const snackbar = ref(false)
const imapMigrationEnabled = computed(
  () => parametersStore.imapMigrationEnabled
)

const notificationTimeout = 2000
const settings = []
const adminMenuItems = [
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
    condition: () => imapMigrationEnabled.value,
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

const menuItems = computed(() => {
  if (route.meta.layout === 'account') {
    return getUserSettingsMenuItems()
  }
  return adminMenuItems
})

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
    if (parametersStore.imapMigrationEnabled === null) {
      parametersApi.getApplication('imap_migration').then((response) => {
        parametersStore.imapMigrationEnabled =
          response.data.params.enabled_imapmigration
      })
    }
  }
})

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
