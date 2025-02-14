<template>
  <ConnectedLayout color="grey" :menu-items="userSettingsMenuItems" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'
import parametersApi from '@/api/parameters'

const authStore = useAuthStore()
const { $gettext } = useGettext()

const applications = ref([])

const authUser = computed(() => authStore.authUser)
const userSettingsMenuItems = computed(() => {
  const result = []
  // Temporary solution...
  const appIcons = {
    contacts: 'mdi-contacts-outline',
  }

  result.push({
    text: $gettext('Settings'),
    to: { name: 'AccountSettings' },
    icon: 'mdi-cog',
  })
  if (authUser.value.mailbox) {
    result.push({
      text: $gettext('Filters'),
      to: { name: 'AccountFilters' },
      icon: 'mdi-filter',
    })
  }
  for (const app of applications.value) {
    result.push({
      icon: appIcons[app.name],
      text: app.label,
      to: { name: 'AccountParametersEdit', params: { app: app.name } },
    })
  }
  return result
})

parametersApi.getUserApplications().then((resp) => {
  applications.value = resp.data
})
</script>
