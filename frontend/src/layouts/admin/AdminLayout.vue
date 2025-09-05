<template>
  <ConnectedLayout :menu-items="adminMenuItems" />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useGlobalStore, useParametersStore } from '@/stores'
import parametersApi from '@/api/parameters'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'
import constants from '@/constants.json'

const { $gettext } = useGettext()
const authStore = useAuthStore()
const globalStore = useGlobalStore()
const parametersStore = useParametersStore()

const isRspamdVisible = ref(false)
const rspamdUrl = ref('/rspamd')
const registeredApplications = ref([])

const authUser = computed(() => authStore.authUser)
const imapMigrationEnabled = computed(
  () => parametersStore.imapMigrationEnabled
)

const openRspamdDashboard = () => {
  window.location = rspamdUrl.value
}

const adminMenuItems = computed(() => {
  const result = [
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
      roles: [
        constants.DOMAIN_ADMIN,
        constants.RESELLER,
        constants.SUPER_ADMIN,
      ],
    },
    {
      text: $gettext('Identities'),
      to: { name: 'Identities' },
      icon: 'mdi-account',
      roles: [
        constants.DOMAIN_ADMIN,
        constants.RESELLER,
        constants.SUPER_ADMIN,
      ],
    },
    {
      text: $gettext('Alarms'),
      to: { name: 'Alarms' },
      icon: 'mdi-bell',
    },
    {
      icon: 'mdi-history',
      text: $gettext('Monitoring'),
      roles: [
        constants.SUPER_ADMIN,
        constants.RESELLER,
        constants.DOMAIN_ADMIN,
      ],
      children: [
        {
          text: $gettext('Statistics'),
          to: { name: 'Statistics' },
          roles: [constants.SUPER_ADMIN],
        },
        {
          text: $gettext('Audit trail'),
          to: { name: 'AuditTrail' },
          roles: [constants.SUPER_ADMIN],
        },
        {
          text: $gettext('Messages'),
          to: { name: 'MessageLog' },
          roles: [
            constants.DOMAIN_ADMIN,
            constants.RESELLER,
            constants.SUPER_ADMIN,
          ],
        },
      ],
    },
    {
      icon: 'mdi-email-sync-outline',
      text: $gettext('IMAP Migration'),
      roles: [constants.SUPER_ADMIN, constants.RESELLER],
      condition: () => imapMigrationEnabled.value,
      children: [
        {
          text: $gettext('Email providers'),
          to: { name: 'ProvidersList' },
          roles: [constants.SUPER_ADMIN, constants.RESELLER],
        },
        {
          text: $gettext('Migrations'),
          to: { name: 'MigrationsList' },
          roles: [constants.RESELLER, constants.SUPER_ADMIN],
        },
      ],
    },
  ]
  const settings = []
  registeredApplications.value.forEach((item) => {
    settings.push({
      text: item.label,
      to: { name: 'ParametersEdit', params: { app: item.name } },
    })
  })
  return result.concat([
    {
      icon: 'mdi-cog',
      text: $gettext('Settings'),
      children: settings,
      roles: [constants.SUPER_ADMIN],
    },
    {
      icon: 'mdi-email-check-outline',
      text: 'Rspamd',
      action: openRspamdDashboard,
      roles: [constants.SUPER_ADMIN],
      condition: () => isRspamdVisible.value,
    },
    {
      icon: 'mdi-information',
      text: $gettext('Information'),
      roles: [constants.SUPER_ADMIN],
      to: { name: 'Information' },
      withBell: true,
    },
  ])
})

if (authUser.value.role === constants.SUPER_ADMIN) {
  let response = await parametersApi.getGlobalApplications()
  registeredApplications.value = response.data

  await globalStore.fetchCapabilities()

  if (globalStore.capabilities.imap_migration) {
    if (parametersStore.imapMigrationEnabled === null) {
      response = await parametersApi.getGlobalApplication('imap_migration')
      parametersStore.imapMigrationEnabled =
        response.data.params.enabled_imapmigration
    }
  }
  isRspamdVisible.value = 'rspamd' in globalStore.capabilities
  if (isRspamdVisible.value) {
    rspamdUrl.value = globalStore.capabilities.rspamd.location || '/rspamd'
  }
}
</script>
