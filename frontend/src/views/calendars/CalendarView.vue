<template>
  <div style="display: grid; grid-template-rows: auto auto 1fr; height: 96vh">
    <div class="text-h5 ml-4 mb-6">
      {{ $gettext('Calendar') }}
    </div>

    <v-toolbar v-if="calendarRef" color="white" flat>
      <v-btn
        class="me-4"
        color="grey-darken-2"
        variant="outlined"
        @click="setToday"
      >
        {{ $gettext('Today') }}
      </v-btn>
      <v-btn
        color="grey-darken-2"
        size="small"
        variant="text"
        icon
        @click="goPrev"
      >
        <v-icon size="small"> mdi-chevron-left </v-icon>
      </v-btn>
      <v-btn
        color="grey-darken-2"
        size="small"
        variant="text"
        icon
        @click="goNext"
      >
        <v-icon size="small"> mdi-chevron-right </v-icon>
      </v-btn>
      <v-toolbar-title>
        {{ calendarRef.title }}
      </v-toolbar-title>
      <v-menu location="bottom end">
        <template #activator="{ props }">
          <v-btn color="grey-darken-2" variant="outlined" v-bind="props">
            <span>{{ typeToLabel[ctype] }}</span>
            <v-icon end> mdi-menu-down </v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item @click="ctype = 'day'">
            <v-list-item-title>{{ $gettext('Day') }}</v-list-item-title>
          </v-list-item>
          <v-list-item @click="ctype = 'week'">
            <v-list-item-title>{{ $gettext('Week') }}</v-list-item-title>
          </v-list-item>
          <v-list-item @click="ctype = 'month'">
            <v-list-item-title>{{ $gettext('Month') }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-toolbar>

    <div style="overflow: auto">
      <v-calendar
        ref="calendarRef"
        v-model="focus"
        :events="events"
        first-day-of-week="1"
        :type="ctype"
        :locale="current"
        event-name="title"
        :event-color="getEventColor"
        :event-ripple="false"
        @mousedown:event="startDrag"
        @mousedown:time="startTime"
        @mousedown:day="startDay"
        @click:day="dayClickCallback"
        @mouseleave="cancelDrag"
        @mousemove:time="mouseMove"
        @mousemove:day="mouseMoveDay"
        @mouseup:time="endDrag"
        @mouseup:day="endDragDay"
        @change="fetchUserEvents"
      >
        <template #event="{ event, timed, eventSummary }">
          <div class="v-event-draggable">
            <component :is="eventSummary"></component>
          </div>
          <div
            v-if="timed"
            class="v-event-drag-bottom"
            @mousedown.stop="extendBottom(event)"
          ></div>
        </template>
      </v-calendar>
    </div>

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
        @refresh-calendar="refreshCalendarEvents"
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
  </div>
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

const { $gettext, current } = useGettext()
const layoutStore = useLayoutStore()
const busStore = useBusStore()

const calendarRef = ref()
const confirm = ref()
const events = ref([])
const selectInfo = ref()
const selectedCalendar = ref(null)
const selectedEvent = ref(null)
const userCalendars = ref([])
const showAccessRulesForm = ref(false)
const showCalendarForm = ref(false)
const showInformation = ref(false)
const showEventForm = ref(false)
const showImportEventsForm = ref(false)
const ctype = ref('week')
const focus = ref('')
const dragEvent = ref(null)
const dragTime = ref(null)
const dragDay = ref(null)
const createEvent = ref(null)
const createStart = ref(null)
const extendOriginal = ref(null)
const updating = ref(false)
const moving = ref(false)

const typeToLabel = {
  day: $gettext('Day'),
  week: $gettext('Week'),
  month: $gettext('Month'),
}

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

async function fetchUserEvents({ start, end }) {
  let newEvents = []
  for (const calendar of userCalendars.value) {
    const resp = await api.getUserCalendarEvents(calendar.pk, {
      start: start.date,
      end: end.date,
    })
    newEvents = newEvents.concat(
      resp.data.map((event) => {
        const newEvent = { ...event }
        newEvent.start = Date.parse(event.start)
        newEvent.end = Date.parse(event.end)
        newEvent.timed = !event.allDay
        return newEvent
      })
    )
  }
  events.value = newEvents
}

const setToday = () => {
  focus.value = ''
}

const goPrev = () => {
  calendarRef.value.prev()
}

const goNext = () => {
  calendarRef.value.next()
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

async function fetchUserCalendars() {
  const resp = await api.getUserCalendars()
  userCalendars.value = resp.data
}

function refreshCalendarEvents() {
  fetchUserEvents({
    start: calendarRef.value.renderProps.start,
    end: calendarRef.value.renderProps.end,
  })
}

const dayClickCallback = (nativeEvent, { date }) => {
  if (!selectedEvent.value) {
    const startDate = new Date(date)
    const endDate = new Date(date)
    selectInfo.value = {
      color: '#2196F3',
      start: startDate,
      end: endDate,
      timed: false,
    }
    showEventForm.value = true
  }
}

async function updateEventDates(calEvent) {
  updating.value = true
  var data = {
    start: DateTime.fromMillis(calEvent.start).toJSDate(),
    end: calEvent.end ? DateTime.fromMillis(calEvent.end).toJSDate() : null,
  }
  const evtCalendar = calEvent.calendar
  if (!calEvent.timed) {
    data.start_date = data.start.toISOString().split('T')[0]
    data.end_date = data.end.toISOString().split('T')[0]
    data.allDay = calEvent.allDay
  } else if (!calEvent.end) {
    const end = DateTime.fromJSDate(data.start)
    end.plus({ hours: 1 })
    data.end = end
  }
  try {
    await api.patchUserEvent(evtCalendar.pk, calEvent.id, data)
    busStore.displayNotification({ msg: $gettext('Event updated') })
  } finally {
    updating.value = false
  }
}

const roundTime = (time, down = true) => {
  const roundTo = 15 // minutes
  const roundDownTime = roundTo * 60 * 1000

  return down
    ? time - (time % roundDownTime)
    : time + (roundDownTime - (time % roundDownTime))
}
const toTime = (tms) => {
  return new Date(
    tms.year,
    tms.month - 1,
    tms.day,
    tms.hour,
    tms.minute
  ).getTime()
}

const getEventColor = (event) => {
  const rgb = parseInt(event.color.substring(1), 16)
  const r = (rgb >> 16) & 0xff
  const g = (rgb >> 8) & 0xff
  const b = (rgb >> 0) & 0xff

  return event === dragEvent.value
    ? `rgba(${r}, ${g}, ${b}, 0.7)`
    : event === createEvent.value
      ? `rgba(${r}, ${g}, ${b}, 0.7)`
      : event.color
}

const startDrag = (nativeEvent, { event, timed }) => {
  if (event) {
    dragEvent.value = event
    if (timed) {
      dragTime.value = null
      extendOriginal.value = null
    } else {
      dragDay.value = null
    }
  }
}

const startTime = (nativeEvent, tms) => {
  const mouse = toTime(tms)

  if (dragEvent.value && dragTime.value === null) {
    const start = dragEvent.value.start

    dragTime.value = mouse - start
  } else {
    createStart.value = roundTime(mouse)
    createEvent.value = {
      title: $gettext('New event'),
      color: '#2196F3',
      start: createStart.value,
      end: createStart.value,
      timed: true,
    }

    events.value.push(createEvent.value)
  }
}

const startDay = (nativeEvent, tms) => {
  const mouse = toTime(tms)

  if (dragEvent.value && dragDay.value === null) {
    dragDay.value = mouse - dragEvent.value.start
  }
}

const mouseMove = (nativeEvent, tms) => {
  const mouse = toTime(tms)

  if (dragEvent.value && dragTime.value !== null) {
    moving.value = true
    const start = dragEvent.value.start
    const end = dragEvent.value.end
    const duration = end - start
    const newStartTime = mouse - dragTime.value
    const newStart = roundTime(newStartTime)
    const newEnd = newStart + duration

    dragEvent.value.start = newStart
    dragEvent.value.end = newEnd
  } else if (createEvent.value && createStart.value !== null) {
    moving.value = true
    const mouseRounded = roundTime(mouse, false)
    const min = Math.min(mouseRounded, createStart.value)
    const max = Math.max(mouseRounded, createStart.value)

    createEvent.value.start = min
    createEvent.value.end = max
  }
}

const mouseMoveDay = (nativeEvent, tms) => {
  const mouse = toTime(tms)
  if (dragEvent.value && dragDay.value !== null) {
    moving.value = true
    const start = dragEvent.value.start
    const end = dragEvent.value.end
    const duration = end - start
    const newStartTime = mouse - dragDay.value
    const newStart = roundTime(newStartTime)
    const newEnd = newStart + duration

    dragEvent.value.start = newStart
    dragEvent.value.end = newEnd
  }
}

const extendBottom = (event) => {
  createEvent.value = event
  createStart.value = event.start
  extendOriginal.value = event.end
}

const endDrag = () => {
  if (createEvent.value && !extendOriginal.value) {
    selectInfo.value = createEvent.value
    showEventForm.value = true
  } else {
    if (moving.value) {
      if (dragEvent.value) {
        updateEventDates(dragEvent.value)
      } else if (createEvent.value) {
        updateEventDates(createEvent.value)
      }
    } else {
      selectedEvent.value = dragEvent.value
      showEventForm.value = true
    }

    dragTime.value = null
    dragEvent.value = null
    createEvent.value = null
    createStart.value = null
    extendOriginal.value = null
    moving.value = false
  }
}

const endDragDay = () => {
  if (dragEvent.value) {
    if (moving.value) {
      updateEventDates(dragEvent.value)
    } else {
      selectedEvent.value = dragEvent.value
      showEventForm.value = true
    }
  }
  dragEvent.value = null
  dragDay.value = null
  moving.value = false
}

const cancelDrag = () => {
  if (createEvent.value) {
    if (extendOriginal.value) {
      createEvent.value.end = extendOriginal.value
    } else {
      const i = events.value.indexOf(createEvent.value)
      if (i !== -1) {
        events.value.splice(i, 1)
      }
    }
  }

  createEvent.value = null
  createStart.value = null
  dragTime.value = null
  dragEvent.value = null
  moving.value = false
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
  await fetchUserCalendars()
  events.value = []
  calendarRef.value.checkChange()
  busStore.displayNotification({ msg: $gettext('Calendar deleted') })
}

watch(
  leftMenuItems,
  (value) => {
    layoutStore.setLeftMenuItems(value)
  },
  { immediate: true }
)

onMounted(() => {
  calendarRef.value.scrollToTime('07:00')
  calendarRef.value.checkChange()
})

await fetchUserCalendars()
</script>

<style scoped>
.v-event-draggable {
  padding-left: 6px;
}

.v-event-timed {
  user-select: none;
  -webkit-user-select: none;
}

.v-event-drag-bottom {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 4px;
  height: 4px;
  cursor: ns-resize;

  &::after {
    display: none;
    position: absolute;
    left: 50%;
    height: 4px;
    border-top: 1px solid white;
    border-bottom: 1px solid white;
    width: 16px;
    margin-left: -8px;
    opacity: 0.8;
    content: '';
  }

  &:hover::after {
    display: block;
  }
}
</style>
