<template>
  <v-card>
    <v-form ref="formRef" @submit.prevent="saveEvent">
      <v-card-title>
        <span class="headline">{{ title }}</span>
      </v-card-title>
      <v-card-text class="py-4">
        <v-alert v-if="readOnly" type="info" variant="tonal" class="mb-4">
          {{
            event.subscription
              ? $gettext(
                  'This event belongs to a calendar you subscribed to, it cannot be modified.'
                )
              : $gettext(
                  'This event belongs to a calendar shared with you in read-only mode.'
                )
          }}
        </v-alert>
        <v-row density="compact">
          <v-col cols="12">
            <v-select
              v-model="form.calendar"
              :items="calendarItems"
              item-title="title"
              item-value="pk"
              :label="$gettext('Calendar')"
              :rules="[rules.required]"
              :error-messages="formErrors.calendar"
              :readonly="readOnly"
              prepend-icon="mdi-calendar"
              hide-details="auto"
              density="compact"
              variant="outlined"
            >
              <template #selection="{ item }">
                <v-icon
                  icon="mdi-circle"
                  :color="item.color"
                  size="x-small"
                  class="mr-2"
                />
                {{ item.title }}
              </template>
              <template #item="{ props: itemProps, item }">
                <v-list-item v-bind="itemProps">
                  <template #prepend>
                    <v-icon
                      icon="mdi-circle"
                      :color="item.color"
                      size="x-small"
                    />
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="form.title"
              :label="$gettext('Title')"
              :rules="[rules.required]"
              :error-messages="formErrors.title"
              :readonly="readOnly"
              prepend-icon="mdi-format-title"
              hide-details="auto"
              density="compact"
              variant="outlined"
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="form.start"
              :label="$gettext('From')"
              :rules="[rules.required]"
              :error-messages="formErrors.start"
              :readonly="readOnly"
              :type="dateType"
              prepend-icon="mdi-clock-outline"
              hide-details="auto"
              density="compact"
              variant="outlined"
            />
          </v-col>
          <!-- Aligned with the fields having an icon once stacked -->
          <v-col cols="12" sm="6" class="pl-10 pl-sm-1">
            <v-text-field
              v-model="form.end"
              :label="$gettext('To')"
              :rules="[rules.required]"
              :error-messages="formErrors.end"
              :readonly="readOnly"
              :type="dateType"
              hide-details="auto"
              density="compact"
              variant="outlined"
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-select
              v-model="form.frequency"
              :items="frequencies"
              :label="$gettext('Repeat')"
              :readonly="readOnly"
              :disabled="recurrenceCustom"
              :loading="loadingRecurrence"
              :hint="
                recurrenceCustom
                  ? $gettext('Custom recurrence, it cannot be modified here')
                  : ''
              "
              :persistent-hint="recurrenceCustom"
              prepend-icon="mdi-repeat"
              hide-details="auto"
              density="compact"
              variant="outlined"
            />
          </v-col>
          <v-col
            v-if="form.frequency !== 'NONE'"
            cols="12"
            sm="6"
            class="pl-10 pl-sm-1"
          >
            <v-text-field
              v-model="form.until"
              :label="$gettext('Until')"
              :error-messages="
                formErrors.recurrence?.until || formErrors.recurrence
              "
              :readonly="readOnly"
              :disabled="recurrenceCustom"
              :clearable="!readOnly && !recurrenceCustom"
              type="date"
              hide-details="auto"
              density="compact"
              variant="outlined"
            />
          </v-col>
          <template v-if="event">
            <v-col cols="12">
              <v-select
                v-model="form.attendees"
                :label="$gettext('Attendees')"
                :items="attendees"
                item-title="display_name"
                item-value="email"
                return-object
                :readonly="readOnly"
                prepend-icon="mdi-account-multiple-outline"
                hide-details="auto"
                variant="outlined"
                density="compact"
                multiple
                chips
                closable-chips
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="form.description"
                :label="$gettext('Description')"
                :readonly="readOnly"
                prepend-icon="mdi-text"
                hide-details="auto"
                auto-grow
                rows="2"
                variant="outlined"
                density="compact"
              />
            </v-col>
          </template>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-if="props.event && !readOnly"
          :loading="working"
          color="error"
          prepend-icon="mdi-delete-outline"
          @click="deleteEvent"
        >
          {{ $gettext('Delete') }}
        </v-btn>
        <v-spacer />
        <v-btn :loading="working" @click="close">{{ $gettext('Close') }}</v-btn>
        <v-btn
          v-if="!readOnly"
          color="primary"
          type="submit"
          :loading="working"
        >
          {{ $gettext('Save') }}
        </v-btn>
      </v-card-actions>
    </v-form>
    <RecurrenceScopeDialog ref="scopeDialog" />
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { DateTime } from 'luxon'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/calendars'
import rules from '@/plugins/rules'
import RecurrenceScopeDialog from '@/components/calendars/RecurrenceScopeDialog'

const props = defineProps({
  info: {
    type: Object,
    default: null,
  },
  event: {
    type: Object,
    default: null,
  },
  // Displayed calendars: own ones and the ones shared with the user
  calendars: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close', 'refreshCalendar'])

const { $gettext } = useGettext()
const busStore = useBusStore()

const attendees = ref([])
const form = ref({})
const formErrors = ref({})
const formRef = ref()
const scopeDialog = ref()
const working = ref(false)
const loadingRecurrence = ref(false)
const recurrenceCustom = ref(false)
// Recurrence as loaded, to only send it when the user changed it
const initialRecurrence = ref('null')

const frequencies = [
  { title: $gettext('Never'), value: 'NONE' },
  { title: $gettext('Every day'), value: 'DAILY' },
  { title: $gettext('Every week'), value: 'WEEKLY' },
  { title: $gettext('Every month'), value: 'MONTHLY' },
  { title: $gettext('Every year'), value: 'YEARLY' },
]

const readOnly = computed(() => props.event?.editable === false)

const title = computed(() => {
  if (readOnly.value) {
    return $gettext('Event')
  }
  return props.event ? $gettext('Edit event') : $gettext('New event')
})

// Calendars the event can be saved in, plus its current one
const calendarItems = computed(() =>
  props.calendars
    .filter((calendar) => calendar.write || calendar.pk === form.value.calendar)
    .map((calendar) => ({
      pk: calendar.pk,
      color: calendar.color,
      title: calendar.owner
        ? `${calendar.name} (${calendar.owner})`
        : calendar.name,
    }))
)

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
        // Own calendars come first
        calendar: props.calendars.find((calendar) => calendar.write)?.pk,
        frequency: 'NONE',
      }
      recurrenceCustom.value = false
      initialRecurrence.value = 'null'
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
      form.value.frequency = 'NONE'
      recurrenceCustom.value = false
      initialRecurrence.value = 'null'
      api.getAttendees().then((resp) => {
        attendees.value = resp.data
      })
      if (value.recurrence_id) {
        loadRecurrence()
      }
    }
  },
  { immediate: true }
)

async function loadRecurrence() {
  loadingRecurrence.value = true
  try {
    // Listed events are expanded occurrences, the rule is on the series
    const resp = await api.getUserEvent(props.event.calendar.pk, props.event.id)
    const recurrence = resp.data.recurrence
    if (recurrence) {
      form.value.frequency = recurrence.frequency
      form.value.until = recurrence.until
        ? DateTime.fromISO(recurrence.until).toISODate()
        : null
      recurrenceCustom.value = recurrence.custom
    }
    initialRecurrence.value = JSON.stringify(getRecurrence())
  } finally {
    loadingRecurrence.value = false
  }
}

function getRecurrence() {
  if (form.value.frequency === 'NONE') {
    return null
  }
  let until = form.value.until || null
  if (until && !form.value.allDay) {
    // Include the occurrence of the last day, in the user's timezone
    until = DateTime.fromISO(until).endOf('day').toISO()
  }
  return { frequency: form.value.frequency, until }
}

function close() {
  formErrors.value = {}
  emit('close')
}
/**
 * For an occurrence of a recurring event, ask the user if the action applies
 * to this occurrence only or to the whole series.
 * Return the parameters to send, or null if the user cancelled.
 */
async function getRecurrenceParams(title) {
  if (!props.event?.recurrence_id) {
    return {}
  }
  const scope = await scopeDialog.value.open(title)
  if (!scope) {
    return null
  }
  return { recurrence_id: props.event.recurrence_id, scope }
}

async function saveEvent() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  const recurrence = getRecurrence()
  const recurrenceChanged =
    JSON.stringify(recurrence) !== initialRecurrence.value
  // A recurrence rule always applies to the whole series
  const recurrenceParams =
    recurrenceChanged && props.event?.recurrence_id
      ? { recurrence_id: props.event.recurrence_id, scope: 'series' }
      : await getRecurrenceParams($gettext('Edit event'))
  if (recurrenceParams === null) {
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
      ...recurrenceParams,
    }
    if (recurrenceChanged) {
      data.recurrence = recurrence
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
      // The event is still stored in its original calendar
      await api.patchUserEvent(props.event.calendar.pk, props.event.id, data)
      busStore.displayNotification({ msg: $gettext('Event updated') })
    }
    emit('refreshCalendar', data.calendar)
    close()
  } catch (error) {
    formErrors.value = error.response?.data || {}
  } finally {
    working.value = false
  }
}

async function deleteEvent() {
  const recurrenceParams = await getRecurrenceParams($gettext('Delete event'))
  if (recurrenceParams === null) {
    return
  }
  working.value = true
  try {
    await api.deleteUserEvent(
      props.event.calendar.pk,
      props.event.id,
      recurrenceParams
    )
    busStore.displayNotification({ msg: $gettext('Event deleted') })
    emit('refreshCalendar', form.value.calendar)
    close()
  } finally {
    working.value = false
  }
}
</script>
