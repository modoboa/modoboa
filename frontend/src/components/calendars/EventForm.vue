<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="saveEvent">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text class="py-4">
        <v-row class="mb-2">
          <v-col cols="12">
            <v-text-field
              v-model="form.title"
              :label="$gettext('Title')"
              :rules="[rules.required]"
              :error-messages="formErrors.title"
              density="compact"
              variant="outlined"
            />
          </v-col>
        </v-row>
        <div class="d-flex mb-3">
          <v-icon icon="mdi-clock-outline" class="mr-4" />
          <v-text-field
            v-model="form.start"
            :label="$gettext('From')"
            :rules="[rules.required]"
            :error-messages="formErrors.start"
            density="compact"
            variant="outlined"
            :type="dateType"
            class="mr-4"
          />
          <v-text-field
            v-model="form.end"
            :label="$gettext('To')"
            :rules="[rules.required]"
            :error-messages="formErrors.end"
            density="compact"
            variant="outlined"
            :type="dateType"
          />
        </div>
        <div class="d-flex mb-3">
          <v-icon icon="mdi-calendar" class="mr-4" />
          <v-select
            v-model="form.calendar"
            :items="userCalendars"
            item-title="name"
            item-value="pk"
            :label="$gettext('Calendar')"
            :rules="[rules.required]"
            :error-messages="formErrors.calendar"
            density="compact"
            variant="outlined"
          />
        </div>
        <template v-if="event">
          <div class="d-flex mb-3">
            <v-icon icon="mdi-account-multiple-outline" class="mr-4" />
            <v-select
              v-model="form.attendees"
              :label="$gettext('Attendees')"
              :items="attendees"
              item-title="display_name"
              item-value="email"
              return-object
              variant="outlined"
              density="compact"
              multiple
              chips
            />
          </div>
          <v-textarea
            v-model="form.description"
            :label="$gettext('Description')"
            auto-grow
            rows="2"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
        </template>
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-if="props.event"
          :loading="working"
          color="error"
          @click="deleteEvent"
        >
          {{ $gettext('Delete') }}
        </v-btn>
        <v-spacer />
        <v-btn :loading="working" @click="close">{{ $gettext('Close') }}</v-btn>
        <v-btn color="primary" type="submit" :loading="working">
          {{ $gettext('Save') }}
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { DateTime } from 'luxon'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/calendars'
import rules from '@/plugins/rules'

const props = defineProps({
  info: {
    type: Object,
    default: null,
  },
  event: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'refreshCalendar'])

const { $gettext } = useGettext()
const busStore = useBusStore()

const attendees = ref([])
const userCalendars = ref([])
const form = ref({})
const formErrors = ref({})
const formRef = ref()
const working = ref(false)

const title = computed(() => {
  return props.event ? $gettext('Edit event') : $gettext('New event')
})

const dateType = computed(() => {
  return form.value.allDay ? 'date' : 'datetime-local'
})

watch(
  () => props.info,
  (value) => {
    if (value) {
      const start =
        typeof value.start === 'number'
          ? DateTime.fromMillis(value.start)
          : DateTime.fromJSDate(value.start)
      const end =
        typeof value.end === 'number'
          ? DateTime.fromMillis(value.end)
          : DateTime.fromJSDate(value.end)
      const format = value.timed ? 'yyyy-MM-dd HH:mm' : 'yyyy-MM-dd'
      form.value = {
        start: start.toFormat(format),
        end: end.toFormat(format),
        allDay: !value.timed,
      }
    }
  },
  { immediate: true }
)

watch(
  () => props.event,
  (value) => {
    if (value) {
      form.value = { ...value }
      form.value.calendar = form.value.calendar.pk
      const format = form.value.timed ? 'yyyy-MM-dd HH:mm' : 'yyyy-MM-dd'
      form.value.start = DateTime.fromMillis(value.start).toFormat(format)
      form.value.end = DateTime.fromMillis(value.end).toFormat(format)
      api.getAttendees().then((resp) => {
        attendees.value = resp.data
      })
    }
  },
  { immediate: true }
)

function close() {
  formErrors.value = {}
  emit('close')
}
async function saveEvent() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  try {
    const data = {
      title: form.value.title,
      description: form.value.description,
      allDay: form.value.allDay,
      attendees: form.value.attendees,
      calendar: form.value.calendar,
    }

    if (data.allDay) {
      data.start_date = form.value.start
      data.end_date = form.value.end
    } else {
      data.start = new Date(form.value.start).toISOString()
      data.end = new Date(form.value.end).toISOString()
    }
    if (!props.event) {
      await api.createUserEvent(form.value.calendar, data)
      busStore.displayNotification({ msg: $gettext('Event added') })
    } else {
      await api.patchUserEvent(form.value.calendar, props.event.id, data)
      busStore.displayNotification({ msg: $gettext('Event updated') })
    }
    emit('refreshCalendar', data.calendar)
    close()
  } finally {
    working.value = false
  }
}

async function deleteEvent() {
  working.value = true
  try {
    await api.deleteUserEvent(form.value.calendar, props.event.id)
    busStore.displayNotification({ msg: $gettext('Event deleted') })
    emit('refreshCalendar', form.value.calendar)
    close()
  } finally {
    working.value = false
  }
}

api.getUserCalendars().then((resp) => {
  userCalendars.value = resp.data
})
</script>
