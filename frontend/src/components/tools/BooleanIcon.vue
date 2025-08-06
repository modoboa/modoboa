<template>
  <v-icon :icon="iconName" :color="iconColor" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: Boolean,
  },
})

const iconName = computed(() => {
  return props.value ? 'mdi-check-circle' : 'mdi-close-circle'
})

const iconColor = computed(() => {
  return props.value ? 'success' : 'error'
})
</script>
