<template>
  <ConnectedLayout :menu-items="adminMenuItems" />
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useParametersStore } from '@/stores'
import parametersApi from '@/api/parameters'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'

const { $gettext } = useGettext()
const authStore = useAuthStore()
const parametersStore = useParametersStore()

const authUser = computed(() => authStore.authUser)
const imapMigrationEnabled = computed(
  () => parametersStore.imapMigrationEnabled
)

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

onMounted(() => {
  if (authUser.value.role === 'SuperAdmins') {
    parametersApi.getGlobalApplications().then((response) => {
      response.data.forEach((item) => {
        settings.push({
          text: item.label,
          to: { name: 'ParametersEdit', params: { app: item.name } },
        })
      })
    })
    if (parametersStore.imapMigrationEnabled === null) {
      parametersApi.getGlobalApplication('imap_migration').then((response) => {
        parametersStore.imapMigrationEnabled =
          response.data.params.enabled_imapmigration
      })
    }
  }
})
</script>
