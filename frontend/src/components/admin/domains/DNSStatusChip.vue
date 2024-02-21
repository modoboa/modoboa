<template>
  <v-chip :color="chipType" size="small">
    {{ label }}
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'

const props = defineProps({
  status: { type: String, default: 'pending' },
})
const { $gettext } = useGettext()

const label = computed(() => {
  if (props.status === 'disabled') {
    return $gettext('Disabled')
  }
  if (props.status === 'pending') {
    return $gettext('Pending')
  }
  if (props.status === 'critical') {
    return $gettext('Problem')
  }
  if (props.status === 'ok') {
    return $gettext('Valid')
  }
  return $gettext('Unknown')
})

const chipType = computed(() => {
  if (props.status === 'disabled') {
    return ''
  }
  if (props.status === 'pending') {
    return 'info'
  }
  if (props.status === 'critical') {
    return 'error'
  }
  if (props.status === 'ok') {
    return 'success'
  }
  return 'warning'
})
</script>
