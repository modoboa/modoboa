<template>
  <v-card class="mt-6">
    <v-data-table-server
      v-model="selected"
      :headers="headers"
      :items="alarms"
      :search="search"
      item-value="id"
      :items-length="totalAlarms"
      :loading="loading"
      elevation="0"
      show-select
      @update:options="fetchAlarms"
    >
      <template #top>
        <v-toolbar color="white" flat>
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            placeholder="Search"
            density="compact"
            variant="outlined"
            hide-details
            flat
            single-line
            class="flex-grow-0 w-33 mr-4"
          ></v-text-field>
          <v-menu location="bottom">
            <template #activator="{ props }">
              <v-btn v-bind="props" size="small">
                {{ $gettext('Actions') }}
                <v-icon right>mdi-chevron-down</v-icon>
              </v-btn>
            </template>
            <v-list density="compact">
              <MenuItems :items="getActionMenuItems()" />
            </v-list>
          </v-menu>
        </v-toolbar>
      </template>
      <template #[`item.status`]="{ item }">
        <v-chip v-if="item.status === 1" color="warning" size="small">
          {{ $gettext('Opened') }}
        </v-chip>
        <v-chip v-else color="info" size="small">
          {{ $gettext('Closed') }}
        </v-chip>
      </template>
      <template #[`item.mailbox`]="{ item }">
        <template v-if="item.mailbox">
          {{ item.mailbox.address }}@{{ item.domain.name }}
        </template>
        <template v-else> / </template>
      </template>
      <template #[`item.created`]="{ item }">
        {{ $date(item.created) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="text-right">
          <v-menu location="bottom">
            <template #activator="{ props }">
              <v-btn icon="mdi-dots-horizontal" v-bind="props" variant="text">
              </v-btn>
            </template>
            <MenuItems :items="getMenuItems(item)" :obj="item" />
          </v-menu>
        </div>
      </template>
    </v-data-table-server>
  </v-card>
</template>

<script setup lang="js">
import { ref } from 'vue'
import debounce from 'debounce'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import alarmsApi from '@/api/alarms'
import constants from '@/constants.json'
import MenuItems from '@/components/tools/MenuItems'

const { $gettext } = useGettext()

const busStore = useBusStore()
const alarms = ref([])
const loading = ref(false)
const search = ref('')
const selected = ref([])
const totalAlarms = ref(0)

const headers = [
  { title: $gettext('Triggered'), key: 'created' },
  { title: $gettext('Status'), key: 'status' },
  { title: $gettext('Domain'), key: 'domain.name', sortable: false },
  { title: $gettext('Mailbox'), key: 'mailbox', sortable: false },
  { title: $gettext('Message'), key: 'title' },
  {
    title: $gettext('Actions'),
    key: 'actions',
    sortable: false,
    align: 'right',
  },
]

function getActionMenuItems() {
  const result = []
  if (selected.value.length > 0) {
    result.push({
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteAlarms,
      color: 'red',
    })
  }
  result.push({
    label: $gettext('Reload'),
    icon: 'mdi-reload',
    onClick: fetchAlarms,
  })
  return result
}

function getMenuItems(item) {
  const result = []
  result.push({
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: deleteAlarm,
    color: 'red',
  })
  if (item.status === constants.ALARM_OPENED) {
    result.push({
      label: $gettext('Close alarm'),
      icon: 'mdi-check',
      onClick: closeAlarm,
      color: 'green',
    })
  } else {
    result.push({
      label: $gettext('Reopen alarm'),
      icon: 'mdi-alert-circle-outline',
      onClick: openAlarm,
      color: 'orange',
    })
  }
  return result
}

function fetchAlarms({ page, itemsPerPage, sortBy }) {
  const params = {
    page: page || 1,
    page_size: itemsPerPage || 10,
  }
  if (sortBy && sortBy.length) {
    params.ordering = sortBy
      .map((item) => (item.order !== 'asc' ? `-${item.key}` : item.key))
      .join(',')
  }
  if (search.value !== '') {
    params.search = search.value
  }
  loading.value = true
  alarmsApi.getAll(params).then((resp) => {
    alarms.value = resp.data.results
    totalAlarms.value = resp.data.count
    loading.value = false
  })
}

async function deleteAlarm(alarm, single = true) {
  alarmsApi.delete(alarm.id).then(() => {
    if (single) {
      busStore.displayNotification({ msg: $gettext('Alarm deleted') })
      fetchAlarms({})
    }
  })
}
async function deleteAlarms() {
  await alarmsApi.bulkDelete(selected.value.map((alarm) => alarm.id))
  busStore.displayNotification({ msg: $gettext('Alarms deleted') })
  selected.value = []
  fetchAlarms({})
}
async function closeAlarm(alarm) {
  alarmsApi
    .switchStatus(alarm.id, { status: constants.ALARM_CLOSED })
    .then(() => {
      busStore.displayNotification({ msg: $gettext('Alarm closed') })
      fetchAlarms({})
    })
}
async function openAlarm(alarm) {
  alarmsApi
    .switchStatus(alarm.id, { status: constants.ALARM_OPENED })
    .then(() => {
      busStore.displayNotification({ msg: $gettext('Alarm re-opened') })
      fetchAlarms({})
    })
}

fetchAlarms = debounce(fetchAlarms, 500)
</script>

<style scoped>
.v-text-field--outlined :deep(fieldset) {
  border-color: #bfc5d2;
}
.v-input--checkbox :deep(.v-label) {
  font-size: 0.875rem !important;
}
</style>
