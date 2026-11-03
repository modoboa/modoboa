<template>
  <v-card class="mt-6">
    <v-data-table-server
      :headers="headers"
      :items="messages"
      :search="search"
      class="elevation-0"
      :items-length="total"
      :items-per-page-options="itemsPerPageOptions"
      @update:options="fetchMessages"
    >
      <template #top>
        <ListToolbar v-model:search="search" />
      </template>
      <template #[`item.date`]="{ item }">
        {{ $date(item.date) }}
      </template>
      <template #[`item.sender`]="{ item }">
        <span :title="item.sender">
          {{ $truncate(item.sender, 50) }}
        </span>
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

const headers = [
  { title: $gettext('Queue ID'), key: 'queue_id' },
  { title: $gettext('Date'), key: 'date', width: '20%' },
  { title: $gettext('Status'), key: 'status' },
  { title: $gettext('To'), key: 'rcpt' },
  { title: $gettext('From'), key: 'sender' },
]
const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

const loading = ref(true)
const messages = ref([])
const search = ref('')
const total = ref(0)

function fetchMessages({ page, itemsPerPage, sortBy, search }) {
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
  logsApi.getMessages(params).then((response) => {
    messages.value = response.data.results
    total.value = response.data.count
    loading.value = false
  })
}

fetchMessages = debounce(fetchMessages, 500)
</script>
