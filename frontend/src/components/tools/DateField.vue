<template>
  <v-menu
    v-model="menu"
    :close-on-content-click="false"
    transition="scale-transition"
    location="bottom"
    min-width="auto"
  >
    <template #activator="{ props }">
      <v-text-field
        :model-value="modelValue"
        :label="label"
        prepend-icon="mdi-calendar"
        readonly
        variant="underlined"
        v-bind="props"
      ></v-text-field>
    </template>
    <v-date-picker :model-value="modelValue" @update:model-value="update">
    </v-date-picker>
  </v-menu>
</template>

<script setup lang="js">
import { ref } from 'vue'

defineProps({
  modelValue: { type: Object, default: null },
  label: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const menu = ref(false)
function update(value) {
  console.log(value)
  emit('update:modelValue', value)
  menu.value = false
}
</script>
