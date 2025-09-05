<template>
  <v-form ref="vFormRef">
    <v-switch
      v-model="model.bypass_virus_checks"
      :label="$gettext('Bypass virus checks')"
    />
  </v-form>
</template>

<script setup>
import { ref } from 'vue'

const model = defineModel()

const vFormRef = ref()

defineExpose({
  vFormRef,
})
</script>
