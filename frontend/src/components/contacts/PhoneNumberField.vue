<template>
  <v-col cols="6">
    <v-text-field
      v-model="phone.number"
      :label="$gettext('Phone number')"
      variant="outlined"
      prepend-icon="mdi-phone"
      density="compact"
    />
  </v-col>
  <v-col cols="4" class="pl-4">
    <v-select
      v-model="phone.type"
      :items="types"
      density="compact"
      variant="outlined"
    />
  </v-col>
  <v-col cols="2" class="pl-4">
    <v-btn icon="mdi-plus" size="x-small" flat @click="$emit('add')" />
    <v-btn
      v-if="index"
      icon="mdi-trash-can"
      color="red"
      size="x-small"
      flat
      variant="text"
      @click="$emit('delete', index)"
    />
  </v-col>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  errors: {
    type: Object,
    default: null,
  },
  index: {
    type: Number,
    required: true,
  },
  modelValue: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['add', 'delete', 'update:modelValue'])

const phone = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

const types = ['cell', 'fax', 'home', 'main', 'pager', 'work', 'other']
</script>
