<template>
  <ConnectedLayout color="grey" :menu-items="getUserSettingsMenuItems()" />
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '@/stores'
import ConnectedLayout from '@/layouts/connected/ConnectedLayout.vue'

const authStore = useAuthStore()
const { $gettext } = useGettext()

const authUser = computed(() => authStore.authUser)

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
</script>
