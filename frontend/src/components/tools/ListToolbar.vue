<template>
  <div class="d-flex flex-column ga-3 pa-4">
    <!-- Wraps on narrow screens instead of clipping, unlike v-toolbar -->
    <div
      v-if="slots.start || slots.actions"
      class="d-flex flex-wrap align-center ga-2"
    >
      <slot name="start" />
      <div class="d-flex flex-wrap align-center ga-2 ms-auto">
        <slot name="actions" />
      </div>
    </div>
    <div class="d-flex flex-wrap align-center ga-2">
      <slot name="search">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          :placeholder="$gettext('Search')"
          variant="outlined"
          hide-details
          single-line
          flat
          density="compact"
          style="flex: 1 1 240px"
        />
      </slot>
      <slot name="filters" />
      <div class="d-flex align-center ga-1 ms-auto">
        <slot name="tools" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSlots } from 'vue'

const search = defineModel('search', { type: String, default: '' })
const slots = useSlots()
</script>
