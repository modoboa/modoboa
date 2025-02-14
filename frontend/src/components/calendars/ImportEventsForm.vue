<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="sendFile">
      <v-card-title>
        <span class="headline">{{ $gettext('Import events') }}</span>
      </v-card-title>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="my-4">
          {{
            $gettext(
              'Select an ICS file to import and click on the Send button'
            )
          }}
        </v-alert>
        <v-file-input
          v-model="file"
          :label="$gettext('Select an ICS file')"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
          :error-messages="formErrors['ics_file']"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :disabled="runningUpload" @click="close">{{
          $gettext('Close')
        }}</v-btn>
        <v-btn type="submit" color="primary" :disabled="runningUpload">
          {{ $gettext('Send') }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useBusStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import api from '@/api/calendars'
import rules from '@/plugins/rules'

const props = defineProps({
  calendar: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'eventsImported'])

const { $ngettext } = useGettext()
const busStore = useBusStore()

const file = ref(null)
const formErrors = ref({})
const formRef = ref()
const runningUpload = ref(false)

function close() {
  formErrors.value = {}
  emit('close')
}

function onSendError(response) {
  formErrors.value = response.data
  runningUpload.value = false
}

async function sendFile() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  let data = new FormData()
  data.append('ics_file', file.value)
  runningUpload.value = true
  try {
    const response = await api.importUserEvents(props.calendar, data)
    close()
    var msg = $ngettext(
      '%{ n } event imported',
      '%{ n } events imported',
      response.data.counter
    )
    busStore.displayNotification({ msg })
    emit('eventsImported', props.calendar)
  } catch (err) {
    onSendError(err.response)
  } finally {
    runningUpload.value = false
  }
}
</script>
