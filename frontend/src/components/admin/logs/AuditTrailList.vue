<template>
  <v-card class="mt-6">
    <v-data-table-server
      v-model:page="page"
      :headers="headers"
      :items="logs"
      :search="search"
      class="elevation-0"
      :items-length="total"
      :items-per-page-options="itemsPerPageOptions"
      :loading="loading"
      mobile-breakpoint="md"
      :row-props="rowProps"
      @update:options="updateOptions"
    >
      <template #top>
        <ListToolbar v-model:search="search">
          <template #filters>
            <v-autocomplete
              v-model="filters.action"
              :items="actions"
              item-title="label"
              item-value="code"
              clearable
              :label="$gettext('Action')"
              variant="outlined"
              hide-details
              density="compact"
              style="flex: 0 1 260px; min-width: 200px"
            />
            <v-autocomplete
              v-model="filters.domain"
              :items="domainsStore.domains"
              item-title="name"
              item-value="name"
              clearable
              :label="$gettext('Domain')"
              variant="outlined"
              hide-details
              density="compact"
              style="flex: 0 1 220px; min-width: 180px"
            />
            <v-date-input
              v-model="period"
              multiple="range"
              clearable
              :label="$gettext('Period')"
              prepend-icon=""
              prepend-inner-icon="$calendar"
              variant="outlined"
              hide-details
              density="compact"
              style="flex: 0 1 280px; min-width: 220px"
            />
          </template>
        </ListToolbar>
      </template>
      <template #[`item.date_created`]="{ item }">
        {{ $date(item.date_created) }}
      </template>
      <template #[`item.action`]="{ item }">
        <div class="d-flex align-center py-2">
          <span class="d-sr-only">{{ item.level }}</span>
          <div class="audit-cell">
            <div v-if="item.action_label" :title="item.message">
              <div class="font-weight-medium">{{ item.action_label }}</div>
              <!-- Not truncated: lists are capped, the "+N" count must stay visible -->
              <div class="text-caption text-medium-emphasis">
                {{ getAuditDetails(item) }}
              </div>
            </div>
            <!-- Entries written before structured fields existed -->
            <div v-else class="text-truncate" :title="item.message">
              {{ item.message }}
            </div>
          </div>
        </div>
      </template>
      <template #[`item.actor_name`]="{ item }">
        <div>{{ item.actor_name }}</div>
        <div v-if="item.ip_address" class="text-caption text-medium-emphasis">
          {{ item.ip_address }}
        </div>
      </template>
    </v-data-table-server>
  </v-card>
</template>

<script setup lang="js">
import { onMounted, reactive, ref, watch } from 'vue'
import ListToolbar from '@/components/tools/ListToolbar.vue'
import { useGettext } from 'vue3-gettext'
import logsApi from '@/api/logs'
import { useDomainsStore } from '@/stores'
import { getAuditDetails } from '@/utils/audit'
import debounce from 'debounce'
import { DateTime } from 'luxon'

const { $gettext } = useGettext()
const loading = ref(false)
const logs = ref([])
const search = ref('')
const total = ref(0)
const page = ref(1)
const actions = ref([])
const filters = reactive({
  action: null,
  domain: null,
  date_from: null,
  date_to: null,
})
// Dates of the selected range, from VDateInput
const period = ref(null)
const domainsStore = useDomainsStore()
// Last pagination/sorting state sent by the table
let options = null

const headers = [
  { title: $gettext('Date'), key: 'date_created', nowrap: true },
  { title: $gettext('Action'), key: 'action' },
  { title: $gettext('Actor'), key: 'actor_name' },
  { title: $gettext('Domain'), key: 'domain' },
]
const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

// INFO is the common case: only flag what deserves attention
const levelClasses = {
  WARNING: 'audit-row audit-row--warning',
  ERROR: 'audit-row audit-row--error',
  CRITICAL: 'audit-row audit-row--error',
}

function rowProps({ item }) {
  return { class: levelClasses[item.level] }
}

function updateOptions(newOptions) {
  options = newOptions
  fetchLogs()
}

function fetchLogs() {
  const { page, itemsPerPage, sortBy, search } = options
  let order
  if (sortBy.length) {
    order = (sortBy[0].order === 'desc' ? '-' : '') + sortBy[0].key
  }
  const activeFilters = Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value)
  )
  const params = {
    ordering: order,
    page: page,
    page_size: itemsPerPage,
    search: search,
    ...activeFilters,
  }
  loading.value = true
  logsApi.getAuditTrail(params).then((response) => {
    logs.value = response.data.results
    total.value = response.data.count
    loading.value = false
  })
}

fetchLogs = debounce(fetchLogs, 500)

watch(period, (dates) => {
  // Local dates: toISOString() would shift them to UTC
  const sorted = (dates || [])
    .map((date) => DateTime.fromJSDate(date))
    .sort((a, b) => a - b)
  filters.date_from = sorted.length ? sorted[0].toISODate() : null
  filters.date_to = sorted.length ? sorted[sorted.length - 1].toISODate() : null
})

watch(filters, () => {
  if (page.value !== 1) {
    // The table emits new options, which reloads the list
    page.value = 1
  } else if (options) {
    fetchLogs()
  }
})

onMounted(async () => {
  domainsStore.getDomains()
  const resp = await logsApi.getAuditActions()
  actions.value = resp.data
})
</script>

<style scoped>
.audit-cell {
  /* Lets text-truncate work in narrow cells */
  min-width: 0;
  max-width: 480px;
}
:deep(.audit-row--warning) {
  --audit-level-color: var(--v-theme-warning);
}
:deep(.audit-row--error) {
  --audit-level-color: var(--v-theme-error);
}
/* Mobile rows stack their cells: color them all to get a continuous bar */
:deep(.audit-row > td:first-child),
:deep(.v-data-table__tr--mobile.audit-row > td) {
  box-shadow: inset 4px 0 0 rgb(var(--audit-level-color));
}
</style>
