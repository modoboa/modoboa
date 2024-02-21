<template>
  <v-card>
    <v-form ref="vform" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text>
        <v-alert variant="tonal" type="info" class="mb-2">
          {{
            $gettext(
              'Provide a CSV file where lines respect one of the following formats:'
            )
          }}
          <slot name="help" />
          {{
            $gettext(
              'The first element of each line is mandatory and must be equal to one of the previous values.'
            )
          }}
          {{ $gettext('You can use a different character as separator.') }}
        </v-alert>
        <label class="m-label">{{ $gettext('Select file') }}</label>
        <v-file-input
          v-model="form.sourcefile"
          accept="text/csv"
          truncate-length="15"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
        />
        <label class="m-label">{{ $gettext('Separator') }}</label>
        <v-text-field
          v-model="form.sepchar"
          :rules="[rules.required]"
          variant="outlined"
          density="compact"
        />
        <v-switch
          v-model="form.continue_if_exists"
          :label="$gettext('Continue on error')"
          color="primary"
          density="compact"
          :hint="$gettext('Don\'t treat duplicated objects as errors')"
          persistent-hint
        />
        <slot name="extraFields" :form="form" />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="close">
          {{ $gettext('Close') }}
        </v-btn>
        <v-btn color="primary" type="submit">
          {{ $gettext('Import') }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules.js'

defineProps({
  helpText: { type: String, default: '' },
  title: { type: String, default: '' },
})

const emit = defineEmits(['close', 'submit'])

const form = ref({})
const vform = ref()

const { $gettext } = useGettext()

function close() {
  form.value = {}
  emit('close')
}

async function submit() {
  const { valid } = await vform.value.validate()
  if (!valid) {
    return
  }
  const data = new FormData()
  data.append('sourcefile', form.value.sourcefile[0])
  if (form.value.sepchar) {
    data.append('sepchar', form.value.sepchar)
  }
  if (form.value.continue_if_exists) {
    data.append('continue_if_exists', form.value.continue_if_exists)
  }
  emit('submit', data, form.value)
}

defineExpose({ close })
</script>
