<template>
  <v-card class="mt-6">
    <v-data-table-server
      v-model="selected"
      :headers="headers"
      :items="messages"
      :search="search"
      :loading="loading"
      :items-length="totalMessages"
      :page="currentPage"
      :items-per-page="itemsPerPageR"
      item-value="mailid"
      elevation="0"
      show-select
      return-object
      density="compact"
      :sort-by="sortByR"
      :row-props="getRowProps"
      :cell-props="getCellProps"
      @update:options="updatedOptions"
      @click:row="openMessage"
    >
      <template #top>
        <div class="d-flex my-4">
          <v-text-field
            v-model="search"
            :placeholder="$gettext('Search in messages')"
            variant="outlined"
            single-line
            flat
            hide-details
            density="compact"
            class="flex-grow-0 w-33 mr-4"
            clearable
            @click:clear="fetchContent"
            @keyup.enter="fetchContent"
          >
            <template #prepend-inner>
              <v-btn icon variant="flat" size="small">
                <v-icon icon="mdi-magnify"></v-icon>
              </v-btn>
            </template>
          </v-text-field>

          <v-btn
            class="ml-2"
            color="success"
            variant="tonal"
            icon="mdi-check"
            size="small"
            :disabled="selected.length === 0"
            :title="$gettext('Release selection')"
            :loading="loading"
            @click="releaseSelection"
          >
          </v-btn>
          <v-btn
            class="ml-2"
            color="error"
            variant="tonal"
            icon="mdi-trash-can"
            size="small"
            :disabled="selected.length === 0"
            :title="$gettext('Delete selection')"
            :loading="loading"
            @click="deleteSelection"
          >
          </v-btn>
          <v-btn
            class="ml-2"
            size="small"
            variant="tonal"
            icon
            :disabled="selected.length === 0"
          >
            <v-icon icon="mdi-cog" />
            <v-menu activator="parent">
              <v-list>
                <v-list-item
                  :title="$gettext('Mark as spam')"
                  @click="markSelectionAsSpam"
                />
                <v-list-item
                  :title="$gettext('Mark as not spam')"
                  @click="markSelectionAsHam"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </div>
      </template>
      <template #[`item.type`]="{ item }">
        <v-chip :color="getTypeColor(item.type)" size="small" label>
          {{ item.type }}
        </v-chip>
      </template>
      <template #[`item.from_address`]="{ item }">
        <span :title="item.from_address">
          {{ $truncate(item.from_address, 30) }}
        </span>
      </template>
      <template #[`item.subject`]="{ item }">
        <span :title="item.subject">
          {{ $truncate(item.subject, 30) }}
        </span>
      </template>
      <template #[`item.datetime`]="{ item }">
        {{ $date(item.datetime) }}
      </template>
    </v-data-table-server>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRouter } from 'vue-router'
import debounce from 'debounce'
import { useBusStore } from '@/stores'
import api from '@/api/amavis'

const { $gettext } = useGettext()
const router = useRouter()
const { displayNotification } = useBusStore()

const currentPage = ref(1)
const itemsPerPageR = ref(10)
const loading = ref(false)
const messages = ref([])
const search = ref('')
const selected = ref([])
const sortByR = ref([])
const totalMessages = ref(0)

const headers = [
  { title: '', key: 'type' },
  { title: $gettext('Score'), key: 'score' },
  { title: $gettext('To'), key: 'to_address' },
  { title: $gettext('From'), key: 'from_address' },
  { title: $gettext('Subject'), key: 'subject' },
  { title: $gettext('Date'), key: 'datetime' },
]

const getRowProps = ({ item }) => {
  return {
    class: item.style,
  }
}

const getCellProps = () => {
  return { class: 'clickable' }
}

const getTypeColor = (value) => {
  if (['S', 'V'].includes(value)) {
    return 'error'
  }
  if (['Y', 'H', 'M', 'B', 'O', 'T'].includes(value)) {
    return 'warning'
  }
  if (value === 'C') {
    return 'success'
  }
  return ''
}

const updatedOptions = async ({ page, itemsPerPage, sortBy }) => {
  currentPage.value = page
  itemsPerPageR.value = itemsPerPage
  sortByR.value = sortBy
  fetchContent()
}

const _fetchContent = async () => {
  loading.value = true
  const params = {
    page: currentPage.value || 1,
    page_size: itemsPerPageR.value || 10,
  }
  if (sortByR.value && sortByR.value.length) {
    params.ordering = sortByR.value
      .map((item) => (item.order !== 'asc' ? `-${item.key}` : item.key))
      .join(',')
  }
  if (search.value !== '') {
    params.search = search.value
  }
  try {
    const resp = await api.getQuarantineContent(params)
    messages.value = resp.data.results
    totalMessages.value = resp.data.count
    selected.value = []
  } finally {
    loading.value = false
  }
}

const fetchContent = debounce(_fetchContent, 500)

const openMessage = (event, { item }) => {
  router.push({
    name: 'QuarantineMessageView',
    params: { mailid: item.mailid, rcpt: item.to_address },
  })
}

const prepareSelectionPayload = () => {
  const data = {
    selection: [],
  }
  for (const row of selected.value) {
    data.selection.push({ rcpt: row.to_address, mailid: row.mailid })
  }
  return data
}

const deleteSelection = async () => {
  loading.value = true
  const data = prepareSelectionPayload()
  try {
    await api.deleteSelection(data)
    fetchContent()
    displayNotification({ msg: $gettext('Selection deleted') })
  } finally {
    loading.value = false
  }
}

const releaseSelection = async () => {
  loading.value = true
  const data = prepareSelectionPayload()
  try {
    const resp = await api.releaseSelection(data)
    fetchContent()
    if (resp.data.status === 'pending') {
      displayNotification({ msg: $gettext('Release request sent') })
    } else {
      displayNotification({ msg: $gettext('Selection released') })
    }
  } finally {
    loading.value = false
  }
}

const markSelection = async (mtype) => {
  loading.value = true
  const data = prepareSelectionPayload()
  data.type = mtype
  try {
    await api.markMessageSelection(data)
    displayNotification({ msg: $gettext('Selection is being processed...') })
    selected.value = []
  } finally {
    loading.value = false
  }
}

const markSelectionAsSpam = async () => {
  await markSelection('spam')
}

const markSelectionAsHam = async () => {
  await markSelection('ham')
}

const submitSearch = () => {}
</script>

<style lang="scss">
.unseen {
  font-weight: bold;
}
.clickable {
  cursor: pointer;
}
</style>
