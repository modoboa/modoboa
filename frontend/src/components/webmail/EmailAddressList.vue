<template>
  <template v-for="(address, index) in addressesSample" :key="address">
    <span v-if="address.name" :title="address.address">{{ address.name }}</span>
    <span v-else>{{ address.address }}</span>
    <span v-if="index < addressesSample.length - 1">, </span>
    <span v-else-if="addressesSample.length < props.addresses.length"
      >, ...</span
    >
  </template>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  addresses: {
    type: Array,
    default: null,
  },
})

const addressesSample = computed(() =>
  props.addresses.length > 2 ? props.addresses.slice(0, 2) : props.addresses
)
</script>
