<template>
  <v-card :title="$gettext('Schedule your sending')">
    <v-card-text>
      <v-form ref="formRef">
        <div class="d-flex">
          <v-date-picker
            v-model="date"
            class="w-50"
            :allowed-dates="allowedDates"
            :rules="[rules.required]"
          />
          <div
            class="w-33 pt-2 text-uppercase text-overline font-weight-regular"
          >
            <label>{{ $gettext('Select time') }}</label>
            <v-text-field
              v-model="time"
              variant="outlined"
              class="mt-6"
              :rules="[rules.required, rules.time]"
            />
          </div>
        </div>
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn :text="$gettext('Close')" :loading="loading" @click="close" />
      <v-btn
        :text="$gettext('Schedule')"
        color="primary"
        :loading="loading"
        @click="submit"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { DateTime } from 'luxon'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import rules from '@/plugins/rules.js'

const props = defineProps({
  initialDate: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'schedule'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const close = () => {
  emit('close')
}

const allowedDates = (value) => {
  const now = new Date()
  return value > now
}

const validateDatetime = (value) => {
  const now = new Date()
  const msg = $gettext('Provided time must be one minute from now at least')
  if (value <= now) {
    displayNotification({ msg, type: 'error' })
    return false
  }
  const delta = value - now
  if (delta / 1000 < 60) {
    displayNotification({ msg, type: 'error' })
    return false
  }
  return true
}

const date = ref('')
const formRef = ref()
const loading = ref(false)
const time = ref('')

const now = DateTime.now()
date.value = now.toJSDate()
time.value = now.toFormat('HH:mm')

const submit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  const datetime = date.value
  const parts = time.value.split(':')
  datetime.setHours(parseInt(parts[0]), parseInt(parts[1]))
  if (!validateDatetime(datetime)) {
    return
  }
  loading.value = true
  emit('schedule', datetime.toISOString())
  emit('close')
  loading.value = false
}

watch(
  () => props.initialDate,
  (value) => {
    if (value) {
      const initialDate = DateTime.fromISO(value)
      date.value = initialDate.toJSDate()
      time.value = initialDate.toFormat('HH:mm')
    }
  },
  { immediate: true }
)
</script>
