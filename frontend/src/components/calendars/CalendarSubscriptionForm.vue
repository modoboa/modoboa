<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="submit">
      <v-card-title>
        <span class="headline">{{
          subscription.pk
            ? $gettext('Edit subscription')
            : $gettext('Subscribe to a calendar')
        }}</span>
      </v-card-title>
      <v-card-text class="py-4">
        <v-text-field
          v-model="subscription.url"
          :label="$gettext('URL')"
          :hint="$gettext('Address of an iCalendar feed (.ics or webcal://)')"
          persistent-hint
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
          :error-messages="formErrors.url"
          class="mb-4"
        />
        <v-text-field
          v-model="subscription.name"
          :label="$gettext('Name')"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
          :error-messages="formErrors.name"
        />
        <ColorField
          v-model="subscription.color"
          :label="$gettext('Color')"
          :rules="[rules.required]"
          :error-messages="formErrors.color"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :loading="working" @click="close">{{ $gettext('Close') }}</v-btn>
        <v-btn color="primary" type="submit" :loading="working">
          {{ subscription.pk ? $gettext('Update') : $gettext('Subscribe') }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import rules from '@/plugins/rules'
import api from '@/api/calendars'
import ColorField from '@/components/tools/ColorField'

const props = defineProps({
  initialSubscription: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close'])

// Default color of new subscriptions (see CalendarSubscription.color)
const DEFAULT_COLOR = '#3a87ad'

const { $gettext } = useGettext()
const busStore = useBusStore()

const subscription = ref(
  props.initialSubscription
    ? { ...props.initialSubscription }
    : { color: DEFAULT_COLOR }
)
const formErrors = ref({})
const formRef = ref()
const working = ref(false)

function close() {
  formErrors.value = {}
  emit('close')
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  try {
    if (subscription.value.pk) {
      await api.updateCalendarSubscription(
        subscription.value.pk,
        subscription.value
      )
      busStore.displayNotification({ msg: $gettext('Subscription updated') })
    } else {
      await api.createCalendarSubscription(subscription.value)
      busStore.displayNotification({ msg: $gettext('Subscription created') })
    }
    close()
  } catch (error) {
    formErrors.value = error.response?.data || {}
  } finally {
    working.value = false
  }
}
</script>
