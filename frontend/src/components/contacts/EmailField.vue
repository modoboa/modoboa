<template>
  <v-col cols="6">
    <v-text-field
      v-model="email.address"
      :label="$gettext('Address')"
      variant="outlined"
      prepend-icon="mdi-email"
      density="compact"
      :rules="[rules.required]"
    />
  </v-col>
  <v-col cols="4" class="pl-4">
    <v-select
      v-model="email.type"
      :items="types"
      density="compact"
      variant="outlined"
      :rules="[rules.required]"
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
import rules from '@/plugins/rules'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
  errors: {
    type: Object,
    default: null,
  },
  index: {
    type: Number,
    required: true,
  },
})
const emit = defineEmits(['add', 'delete', 'update:modelValue'])

const email = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

const types = ['home', 'work', 'other']
</script>
