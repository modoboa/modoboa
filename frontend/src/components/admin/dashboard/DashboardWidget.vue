<template>
  <v-alert
    v-if="error"
    type="error"
    variant="tonal"
    :text="$gettext('Unable to load this widget')"
  />
  <Suspense v-else>
    <slot />
    <template #fallback>
      <v-skeleton-loader :type="skeleton" />
    </template>
  </Suspense>
</template>

<script setup>
import { onErrorCaptured, ref } from 'vue'

defineProps({
  skeleton: { type: String, default: 'heading, list-item@3' },
})

const error = ref(false)

// Keep a failing widget from taking the whole dashboard down
onErrorCaptured((err) => {
  console.error(err)
  error.value = true
  return false
})
</script>
