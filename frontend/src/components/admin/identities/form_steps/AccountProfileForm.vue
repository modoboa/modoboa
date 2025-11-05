<template>
  <v-form ref="vFormRef">
    <label class="m-label">{{ $gettext('Language') }}</label>
    <v-autocomplete
      v-model="model.language"
      :items="languageStore.availableLanguages"
      item-title="label"
      item-value="code"
      variant="outlined"
      density="compact"
      :error-messages="languageError"
    />
    <label class="m-label">{{ $gettext('Phone number') }}</label>
    <v-text-field
      v-model="model.phone_number"
      variant="outlined"
      density="compact"
    />
    <label class="m-label">{{ $gettext('Secondary email') }}</label>
    <v-text-field
      v-model="model.secondary_email"
      variant="outlined"
      density="compact"
      :rules="[rules.emailOrNull]"
    />
  </v-form>
</template>

<script setup>
import { ref } from 'vue'
import { useLanguageStore } from '@/stores'
import rules from '@/plugins/rules'

const model = defineModel({
  type: Object,
})

const languageStore = useLanguageStore()

const languageError = ref('')
const vFormRef = ref()

defineExpose({ vFormRef })
</script>
