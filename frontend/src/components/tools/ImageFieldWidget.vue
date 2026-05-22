<template>
  <div>
    <label v-if="label" class="m-label">{{ label }}</label>
    <div v-if="modelValue" class="mb-2">
      <v-img :src="modelValue" max-height="80" max-width="240" contain />
    </div>
    <div v-else class="text-medium-emphasis mb-2">
      {{ $gettext('No custom image, default will be used.') }}
    </div>
    <div class="d-flex align-center ga-2">
      <v-file-input
        :model-value="fileInput"
        :label="$gettext('Upload image')"
        accept="image/*"
        :loading="uploading"
        :disabled="disabled"
        :error="!!errorMessage"
        :error-messages="errorMessage"
        truncate-length="20"
        variant="outlined"
        density="compact"
        hide-details
        class="flex-grow-1"
        @update:model-value="onFilePicked"
      />
      <v-btn
        v-if="modelValue"
        icon="mdi-close"
        variant="text"
        size="small"
        :loading="clearing"
        :disabled="disabled"
        :title="$gettext('Remove image')"
        @click="emit('clear')"
      />
    </div>
    <div v-if="helpText" class="text-medium-emphasis text-caption mt-1">
      {{ helpText }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  helpText: { type: String, default: '' },
  uploading: { type: Boolean, default: false },
  clearing: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  errorMessage: { type: [String, Array], default: undefined },
})

const emit = defineEmits(['upload', 'clear'])

const { $gettext } = useGettext()

// Locally control the file input so the "selected file" chip can be reset
// after the parent finishes handling the upload (Vuetify keeps the picked
// filename otherwise).
const fileInput = ref(null)

function onFilePicked(file) {
  if (!file) {
    return
  }
  emit('upload', file)
}

// When the parent stops the loading state, clear the chip — covers both
// success and failure paths uniformly.
watch(
  () => props.uploading,
  (isUploading, wasUploading) => {
    if (wasUploading && !isUploading) {
      fileInput.value = null
    }
  }
)
</script>
