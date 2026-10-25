<template>
  <v-autocomplete
    v-model="model"
    :items="items"
    :item-title="getTitle"
    item-value="name"
    return-object
    density="compact"
    variant="outlined"
    hide-details
    :label="$gettext('Domain')"
    style="max-width: 250px"
  />
</template>

<script setup>
import { computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useDomainsStore } from '@/stores'
import constants from '@/constants.json'

const model = defineModel({ type: Object, default: null })

const { $gettext } = useGettext()
const authStore = useAuthStore()
const domainsStore = useDomainsStore()

// "global" is the name of the server wide statistics file
const GLOBAL = { name: 'global' }

const items = computed(() =>
  authStore.authUser.role === constants.SUPER_ADMIN
    ? [GLOBAL, ...domainsStore.domains]
    : domainsStore.domains
)

function getTitle(item) {
  return item === GLOBAL ? $gettext('Global') : item.name
}

watch(
  items,
  (value) => {
    if (!model.value && value.length) {
      model.value = value[0]
    }
  },
  { immediate: true }
)

if (!domainsStore.domainsLoaded) {
  domainsStore.getDomains()
}
</script>
