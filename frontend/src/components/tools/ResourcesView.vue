<template>
  <v-card>
    <v-card-title>
      <span class="headline">{{ $gettext('Resources usage') }}</span>
    </v-card-title>
    <v-card-text>
      <div v-for="resource in resources" :key="resource.name" class="mt-4">
        {{ resource.label }} ({{ Math.ceil(resource.usage) }}%)
        <v-progress-linear
          :value="resource.usage"
          :color="getProgressColor(resource.usage)"
        />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="js">
defineProps({
  resources: { type: Array, default: null },
})

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
