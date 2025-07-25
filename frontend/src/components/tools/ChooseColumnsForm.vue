<template>
  <v-card :title="$gettext('Choose columns to display')">
    <v-card-text>
      <div v-for="column in props.availableColumns" :key="column.key">
        <v-checkbox
          v-model="model"
          :value="column.key"
          :label="column.title"
          color="primary"
          hide-details
          density="compact"
          :disabled="props.mandatoryColumns.includes(column.key)"
        />
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn color="primary" variant="outlined" @click="apply">
        {{ $gettext('Apply') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const props = defineProps({
  availableColumns: {
    type: Array,
    default: null,
  },
  mandatoryColumns: {
    type: Array,
    default: null,
  },
  columns: {
    type: Array,
    default: null,
  },
})
const model = defineModel({ type: Array })
const emit = defineEmits(['apply'])

const apply = () => {
  emit('apply', model.value)
}

model.value = props.columns.map((col) => col.key)
</script>
