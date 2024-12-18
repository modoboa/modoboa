<template>
  <v-card class="mt-6">
    <v-data-table-server
      :headers="headers"
      :items="logs"
      :search="search"
      class="elevation-0"
      :items-length="total"
      @update:options="fetchLogs"
    >
      <template #top>
        <v-toolbar flat color="white">
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            :placeholder="$gettext('Search')"
            variant="outlined"
            hide-details
            density="compact"
            class="flex-grow-0 w-33"
          />
        </v-toolbar>
      </template>
      <template #[`item.level`]="{ item }">
        <v-chip
          :color="getLevelColor(item.level)"
          text-color="white"
          size="small"
        >
          {{ item.level }}
        </v-chip>
      </template>
    </v-data-table-server>
  </v-card>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import logsApi from '@/api/logs'
import debounce from 'debounce'

const { $gettext } = useGettext()
const loading = ref(false)
const logs = ref([])
const search = ref('')
const total = ref(0)

const headers = [
  { title: $gettext('Date'), key: 'date_created' },
  { title: $gettext('Level'), key: 'level' },
  { title: $gettext('Logger'), key: 'logger' },
  { title: $gettext('Message'), key: 'message' },
]

function getLevelColor(level) {
  if (level === 'INFO') {
    return 'primary'
  }
  if (level === 'WARNING') {
    return 'orange'
  }
  if (level === 'CRITICAL' || level === 'ERROR') {
    return 'red'
  }
  return ''
}

function fetchLogs({ page, itemsPerPage, sortBy, search }) {
  let order
  if (sortBy.length) {
    order = (sortBy[0].order === 'desc' ? '-' : '') + sortBy[0].key
  }
  const params = {
    ordering: order,
    page: page,
    page_size: itemsPerPage,
    search: search,
  }
  loading.value = true
  logsApi.getAuditTrail(params).then((response) => {
    logs.value = response.data.results
    total.value = response.data.count
    loading.value = false
  })
}

fetchLogs = debounce(fetchLogs, 500)
</script>
