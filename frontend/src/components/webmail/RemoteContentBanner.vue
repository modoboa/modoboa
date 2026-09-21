<template>
  <v-alert
    class="remote-content-banner mb-2"
    type="info"
    variant="tonal"
    density="compact"
    icon="mdi-image-off-outline"
  >
    <div class="d-flex align-center flex-wrap ga-2">
      <span class="flex-1-1">
        {{
          $gettext('Remote images have been blocked to protect your privacy.')
        }}
      </span>
      <v-btn size="small" variant="text" @click="$emit('show')">
        {{ $gettext('Display images') }}
      </v-btn>
    </div>
  </v-alert>
</template>

<script setup>
defineEmits(['show'])
</script>
