<template>
  <v-card class="mt-6">
    <v-data-table-server
      :headers="headers"
      :items="logs"
      :search="search"
      class="elevation-0"
      :items-length="total"
      :items-per-page-options="itemsPerPageOptions"
      mobile-breakpoint="md"
      :row-props="rowProps"
      @update:options="fetchLogs"
    >
      <template #top>
        <ListToolbar v-model:search="search" />
      </template>
      <template #[`item.action`]="{ item }">
        <div class="d-flex align-center py-2">
          <span class="d-sr-only">{{ item.level }}</span>
          <div class="audit-cell">
            <div v-if="item.action_label" :title="item.message">
              <div class="font-weight-medium">{{ item.action_label }}</div>
              <div class="text-caption text-medium-emphasis text-truncate">
                {{ item.object_repr }}
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
import { ref } from 'vue'
import ListToolbar from '@/components/tools/ListToolbar.vue'
import { useGettext } from 'vue3-gettext'
import logsApi from '@/api/logs'
import debounce from 'debounce'

const { $gettext } = useGettext()
const loading = ref(false)
const logs = ref([])
const search = ref('')
const total = ref(0)

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
