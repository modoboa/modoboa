<template>
  <v-dialog v-model="dialog" max-width="450" @keydown.esc="choose(null)">
    <v-card>
      <v-toolbar color="primary" density="compact" variant="flat">
        <v-toolbar-title class="text-body-medium font-weight-bold">
          {{ title }}
        </v-toolbar-title>
      </v-toolbar>
      <v-card-text class="pa-4">
        {{ $gettext('This event is part of a recurring series.') }}
      </v-card-text>
      <v-card-actions class="pt-3">
        <v-btn @click="choose(null)">
          {{ $gettext('Cancel') }}
        </v-btn>
        <v-spacer />
        <v-btn color="primary" @click="choose('occurrence')">
          {{ $gettext('This event') }}
        </v-btn>
        <v-btn color="primary" @click="choose('series')">
          {{ $gettext('All events') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'

const dialog = ref(false)
const title = ref('')
let storedResolve

/**
 * Ask which occurrences of a recurring event an action applies to.
 * Resolve with 'occurrence', 'series' or null (cancelled).
 */
function open(_title) {
  title.value = _title
  dialog.value = true
  return new Promise((resolve) => {
    storedResolve = resolve
  })
}
defineExpose({
  open,
})

function choose(scope) {
  storedResolve(scope)
  dialog.value = false
}
</script>
