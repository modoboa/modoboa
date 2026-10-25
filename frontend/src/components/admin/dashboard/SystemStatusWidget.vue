<template>
  <v-card :title="$gettext('System')">
    <v-card-text>
      <div class="mb-2">Modoboa {{ core?.version }}</div>
      <v-alert
        v-if="updateCount"
        type="success"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ $gettext('%{ count } update(s) available', { count: updateCount }) }}
      </v-alert>
      <v-alert
        v-for="notification in globalStore.adminNotifications"
        :key="notification.id"
        :type="notification.color"
        variant="tonal"
        density="compact"
        class="mb-2"
        :text="notification.text"
      />
    </v-card-text>
    <v-card-actions class="justify-center">
      <v-btn :to="{ name: 'Information' }" variant="text" color="primary">
        {{ $gettext('More information') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGlobalStore } from '@/stores'
import adminApi from '@/api/admin'

const globalStore = useGlobalStore()
const components = ref([])

const core = computed(() => components.value.find((c) => c.name === 'modoboa'))
const updateCount = computed(
  () => components.value.filter((c) => c.update).length
)

const resp = await adminApi.getComponentsInformation()
components.value = resp.data
</script>
