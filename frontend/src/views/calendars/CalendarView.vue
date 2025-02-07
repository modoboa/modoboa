<template>
  <div class="text-h5 ml-4 mb-6">
    {{ $gettext('Calendar') }}
  </div>
  <FullCalendar ref="calendarRef" :options="calendarOptions" />

  <v-dialog v-model="showInformation" persistent max-width="800px">
    <CalendarDetail :calendar="selectedCalendar" @close="closeInformation" />
  </v-dialog>
  <v-dialog v-model="showCalendarForm" persistent max-width="800px">
    <CalendarForm
      :initial-calendar="selectedCalendar"
      @color-changed="refreshCalendarEvents"
      @close="closeCalendarForm"
    />
  </v-dialog>
  <v-dialog v-model="showEventForm" persistent max-width="800px">
    <EventForm
      :info="selectInfo"
      :event="selectedEvent"
      @close="closeEventForm"
    />
  </v-dialog>
  <v-dialog v-model="showAccessRulesForm" persistent max-width="800px">
    <CalendarAccessRulesForm
      v-if="selectedCalendar"
      :calendar-pk="selectedCalendar.pk"
      @close="closeAccessRulesForm"
    />
  </v-dialog>
  <v-dialog v-model="showImportEventsForm" persistent max-width="800px">
    <ImportEventsForm
      v-if="selectedCalendar"
      :calendar="selectedCalendar"
      @events-imported="refreshCalendarEvents"
      @close="closeImportEventsForm"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useLayoutStore } from '@/stores'
import { useBusStore } from '@/stores'
import { DateTime } from 'luxon'
import api from '@/api/calendars'
import CalendarAccessRulesForm from '@/components/calendars/CalendarAccessRulesForm'
import CalendarForm from '@/components/calendars/CalendarForm'
import CalendarDetail from '@/components/calendars/CalendarDetail'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import EventForm from '@/components/calendars/EventForm'
import ImportEventsForm from '@/components/calendars/ImportEventsForm'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import timeGridPlugin from '@fullcalendar/timegrid'

const { $gettext, current } = useGettext()
const layoutStore = useLayoutStore()
const busStore = useBusStore()

const calendarRef = ref()
const confirm = ref()
const selectInfo = ref()
const selectedCalendar = ref(null)
const selectedEvent = ref(null)
const userCalendars = ref([])
const showAccessRulesForm = ref(false)
const showCalendarForm = ref(false)
const showInformation = ref(false)
const showEventForm = ref(false)
const showImportEventsForm = ref(false)

const leftMenuItems = computed(() => {
  const result = [
    {
      icon: 'mdi-plus',
      text: $gettext('New calendar'),
      action: openCalendarForm,
    },
    {
      text: $gettext('My calendars'),
      subheader: true,
    },
  ]
  for (const calendar of userCalendars.value) {
    result.push({
      text: calendar.name,
      children: [
        {
          text: $gettext('Information'),
          icon: 'mdi-information-outline',
          action: () => openInformation(calendar),
        },
        {
          text: $gettext('Edit'),
          icon: 'mdi-pencil',
          action: () => editCalendar(calendar),
        },
        {
          text: $gettext('Access rules'),
          icon: 'mdi-filter-outline',
          action: () => openAccessRulesForm(calendar),
        },
        {
          text: $gettext('Delete'),
          icon: 'mdi-trash-can-outline',
          action: () => deleteCalendar(calendar.pk),
        },
        {
          text: $gettext('Import'),
          icon: 'mdi-calendar-import-outline',
          action: () => openImportEventsForm(calendar),
        },
      ],
    })
  }
  return result
})

async function fetchUserCalendarEvents(
  calendarPk,
  info,
  successCallback,
  failureCallback
) {
  try {
    const resp = await api.getUserCalendarEvents(calendarPk, {
      start: info.startStr,
      end: info.endStr,
    })
    successCallback(resp.data)
  } catch (err) {
    failureCallback(err)
  }
}

function openCalendarForm() {
  showCalendarForm.value = true
}

function closeCalendarForm() {
  selectedCalendar.value = null
  showCalendarForm.value = false
  fetchUserCalendars()
}

function openInformation(calendar) {
  selectedCalendar.value = calendar
  showInformation.value = true
}

function closeInformation() {
  selectedCalendar.value = null
  showInformation.value = false
}

function openAccessRulesForm(calendar) {
  selectedCalendar.value = calendar
  showAccessRulesForm.value = true
}

function closeAccessRulesForm() {
  selectedCalendar.value = null
  showAccessRulesForm.value = false
}

function openImportEventsForm(calendar) {
  selectedCalendar.value = calendar
  showImportEventsForm.value = true
}

function closeImportEventsForm() {
  selectedCalendar.value = null
  showImportEventsForm.value = false
}

function fetchUserCalendars() {
  api.getUserCalendars().then((resp) => {
    userCalendars.value = resp.data
  })
}

function refreshCalendarEvents(calendar) {
  const fullc = calendarRef.value.getApi()
  const evtSource = fullc.getEventSourceById(`user-${calendar.pk}`)
  evtSource.refetch()
}

function selectCallback(info) {
  selectInfo.value = info
  showEventForm.value = true
}

async function eventClickCallback(info) {
  const resp = await api.getUserEvent(
    info.event.extendedProps.calendar.pk,
    info.event.id
  )
  selectedEvent.value = resp.data
  showEventForm.value = true
}

function updateEventDates(calEvent) {
  var data = {
    start: calEvent.start,
    end: calEvent.end,
  }
  const evtCalendar = calEvent.extendedProps.calendar
  if (calEvent.allDay) {
    const end = DateTime.fromJSDate(data.start)
    end.plus({ days: 1 })
    data.start.setHours(0, 0, 0)
    data.end = end
    data.allDay = calEvent.allDay
  } else if (!calEvent.end) {
    const end = DateTime.fromJSDate(data.start)
    end.plus({ hours: 1 })
    data.end = end
  }
  api.patchUserEvent(evtCalendar.pk, calEvent.id, data).then((response) => {
    busStore.displayNotification({ msg: $gettext('Event updated') })
  })
}
function eventDropCallback(info) {
  updateEventDates(info.event)
}
function eventResizeCallback(info) {
  updateEventDates(info.event)
}

function closeEventForm() {
  showEventForm.value = false
  selectedEvent.value = null
}

function editCalendar(calendar) {
  selectedCalendar.value = calendar
  showCalendarForm.value = true
}

async function deleteCalendar(calendarPk) {
  const result = await confirm.value.open(
    $gettext('Warning'),
    $gettext('Do you really want to delete this calendar?'),
    { color: 'warning' }
  )
  if (!result) {
    return
  }
  await api.deleteUserCalendar(calendarPk)
  const fullc = calendarRef.value.getApi()
  const evtSource = fullc.getEventSourceById(`user-${calendar.pk}`)
  evtSource.remove()
  busStore.displayNotification({ msg: $gettext('Calendar deleted') })
}

const calendarOptions = {
  plugins: [timeGridPlugin, dayGridPlugin, interactionPlugin],
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
  scrollTime: '09:00:00',
  height: '100%',
  firstDay: 1,
  initialView: 'timeGridWeek',
  locale: current,
  selectable: true,
  selectMirror: true,
  editable: true,
  dayMaxEventRows: true,
  businessHours: {
    daysOfWeek: [1, 2, 3, 4, 5],
    startTime: '09:00',
    endTime: '18:00',
  },
  select: selectCallback,
  eventClick: eventClickCallback,
  eventDrop: eventDropCallback,
  eventResize: eventResizeCallback,
}

watch(
  leftMenuItems,
  (value) => {
    layoutStore.setLeftMenuItems(value)
  },
  { immediate: true }
)

watch(userCalendars, (value) => {
  const fullc = calendarRef.value.getApi()
  if (!fullc) {
    return
  }
  for (const calendar of value) {
    const evtSource = fullc.getEventSourceById(`user-${calendar.pk}`)
    if (!evtSource) {
      fullc.addEventSource({
        id: `user-${calendar.pk}`,
        events: fetchUserCalendarEvents.bind(this, calendar.pk),
      })
    }
  }
})

onMounted(() => {
  fetchUserCalendars()
})
</script>
