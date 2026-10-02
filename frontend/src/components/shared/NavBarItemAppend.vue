<template>
  <v-badge
    v-if="item.withBell"
    dot
    inline
    color="secondary"
    :class="{ 'mr-2': item.badge }"
  />
  <v-chip
    v-if="item.badge"
    size="x-small"
    color="secondary"
    variant="flat"
    class="font-weight-bold"
  >
    {{ item.badge }}
  </v-chip>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    required: true,
  },
})
</script>
