<template>
  <v-form ref="vFormRef">
    <template v-for="resource in resources" :key="resource.name">
      <label class="m-label">{{ resource.label }}</label>
      <v-text-field
        v-model="resource.max_value"
        type="number"
        variant="outlined"
        dense
        :rules="[rules.required]"
      />
    </template>
  </v-form>
</template>

<script setup lang="js">
import { ref, computed } from 'vue'
import rules from '@/plugins/rules'

const props = defineProps({ modelValue: { type: Object, default: null } })

const resources = computed(() => props.modelValue)

const vFormRef = ref()

function getPayload() {
  return resources.value.map((r) => {
    return { name: r.name, max_value: r.max_value }
  })
}

defineExpose({ vFormRef, getPayload })
</script>
