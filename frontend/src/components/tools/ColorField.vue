<template>
  <v-text-field
    :model-value="modelValue"
    :label="label || undefined"
    :hint="hint"
    :error="errorMessages !== undefined && errorMessages !== null"
    :error-messages="errorMessages"
    placeholder="#aabbcc"
    persistent-hint
    clearable
    density="compact"
    variant="outlined"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #prepend-inner>
      <v-menu
        v-model="pickerOpen"
        :close-on-content-click="false"
        location="bottom start"
      >
        <template #activator="{ props: activatorProps }">
          <div
            class="m-color-swatch"
            :style="{ backgroundColor: modelValue || '#fff' }"
            v-bind="activatorProps"
          />
        </template>
        <v-color-picker
          :model-value="modelValue || '#000000'"
          mode="hex"
          flat
          @update:model-value="(v) => emit('update:modelValue', v)"
        />
      </v-menu>
    </template>
  </v-text-field>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  errorMessages: { type: [String, Array], default: undefined },
})

const emit = defineEmits(['update:modelValue'])

// Picker visibility is intentionally local to each instance so two
// ColorFields on the same screen don't share a single open/close state.
const pickerOpen = ref(false)
</script>

<style scoped>
.m-color-swatch {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  cursor: pointer;
}
</style>
