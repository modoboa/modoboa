<template>
  <div class="d-flex flex-column flex-grow-1">
    <HtmlEditor
      v-if="htmlMode"
      v-model="model"
      class="d-flex flex-column flex-grow-1"
    />
    <v-textarea
      v-else
      v-model="model"
      variant="outlined"
      class="flex-grow-1"
      :placeholder="$gettext('Write your message here...')"
      auto-grow
      rows="15"
    />
  </div>
</template>

<script setup>
import HtmlEditor from '@/components/tools/HtmlEditor'

// The plain/HTML toggle lives in the compose toolbar; the mode is owned by
// the parent and bound here (v-model:html-mode).
defineProps({
  htmlMode: {
    type: Boolean,
    default: false,
  },
})

const model = defineModel()
</script>
