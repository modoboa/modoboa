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
            type="datetime-local"
            class="mr-4"
          />
          <v-text-field
            v-model="form.end"
            :label="$gettext('To')"
            :rules="[rules.required]"
            :error-messages="formErrors.end"
            density="compact"
            variant="outlined"
            type="datetime-local"
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
        <v-spacer />
        <v-btn @click="close">{{ $gettext('Close') }}</v-btn>
        <v-btn color="primary" type="submit">
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
const emit = defineEmits(['close'])

const { $gettext } = useGettext()
const busStore = useBusStore()

const attendees = ref([])
const userCalendars = ref([])
const form = ref({})
const formErrors = ref({})
const formRef = ref()

const title = computed(() => {
  return props.event ? $gettext('Edit event') : $gettext('New event')
})

watch(
  () => props.info,
  (value) => {
    if (value) {
      form.value = {
        start: DateTime.fromISO(value.startStr).toFormat('yyyy-MM-dd HH:mm'),
        end: DateTime.fromISO(value.endStr).toFormat('yyyy-MM-dd HH:mm'),
        allDay: value.allDay,
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
      form.value.start = DateTime.fromISO(value.start).toFormat(
        'yyyy-MM-dd HH:mm'
      )
      form.value.end = DateTime.fromISO(value.end).toFormat('yyyy-MM-dd HH:mm')
      console.log(form.value)
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
  var data = JSON.parse(JSON.stringify(form.value))
  if (!props.event) {
    api.createUserEvent(form.value.calendar, data).then(() => {
      busStore.displayNotification({ msg: $gettext('Event added') })
      close()
    })
  } else {
    api.patchUserEvent(form.value.calendar, props.event.id, data).then(() => {
      busStore.displayNotification({ msg: $gettext('Event updated') })
      close()
    })
  }
}

api.getUserCalendars().then((resp) => {
  userCalendars.value = resp.data
})
</script>
