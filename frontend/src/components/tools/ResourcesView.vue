<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Resources usage') }}</span>
    </v-card-title>
    <v-card-text>
      <div v-for="resource in resources" :key="resource.name" class="mt-4">
        <template v-if="resource.max_value === -1">
          {{ resource.label }} ({{ $gettext('Unlimited') }})
        </template>
        <template v-else-if="resource.max_value === 0">
          {{ resource.label }} ({{ noLimitLabel(resource) }})
        </template>
        <template v-else>
          {{ resource.label }} ({{ Math.ceil(resource.usage) }}%)
          <v-progress-linear
            :model-value="resource.usage"
            :color="getProgressColor(resource.usage)"
          />
        </template>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { useGettext } from 'vue3-gettext'

defineProps({
  resources: { type: Array, default: null },
})

const { $gettext } = useGettext()

const noLimitLabel = (resource) => {
  if (resource.name === 'quota') {
    return $gettext('No quota')
  }
  return $gettext('Creation denied')
}

function getProgressColor(value) {
  if (value < 50) {
    return 'primary'
  }
  if (value < 80) {
    return 'warning'
  }
  return 'error'
}
</script>
