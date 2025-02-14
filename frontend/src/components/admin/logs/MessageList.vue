<template>
  <v-card class="mt-6">
    <v-data-table-server
      :headers="headers"
      :items="messages"
      :search="search"
      class="elevation-0"
      :items-length="total"
      @update:options="fetchMessages"
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
      <template #[`item.date`]="{ item }">
        {{ $date(item.date) }}
      </template>
      <template #[`item.sender`]="{ item }">
        {{ $truncate(item.sender, 50) }}
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

const headers = [
  { title: $gettext('Queue ID'), key: 'queue_id' },
  { title: $gettext('Date'), key: 'date', width: '20%' },
  { title: $gettext('Status'), key: 'status' },
  { title: $gettext('To'), key: 'rcpt' },
  { title: $gettext('From'), key: 'sender' },
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
