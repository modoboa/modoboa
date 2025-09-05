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
            hide-details
            class="flex-grow-0 w-33 mr-4"
            clearable
            density="compact"
            @click:clear="fetchContent"
            @keyup.enter="fetchContent"
          >
            <template #prepend-inner>
              <v-btn icon variant="flat" size="small">
                <v-icon icon="mdi-magnify"></v-icon>
                <v-menu activator="parent">
                  <v-card>
                    <v-card-text>
                      <v-radio-group v-model="searchCriteria">
                        <v-radio
                          :label="$gettext('From address')"
                          value="from_addr"
                        ></v-radio>
                        <v-radio
                          :label="$gettext('Subject')"
                          value="subject"
                        ></v-radio>
                        <v-radio :label="$gettext('To')" value="to"></v-radio>
                        <v-radio
                          :label="$gettext('both')"
                          value="both"
                        ></v-radio>
                      </v-radio-group>
                    </v-card-text>
                  </v-card>
                </v-menu>
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
            v-if="manualLearningEnabled"
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

          <v-select
            v-model="typeFilter"
            variant="outlined"
            :items="messageTypes"
            class="ml-2 flex-grow-0"
            density="compact"
            item-title="label"
            item-value="key"
            chips
            hide-details
            @update:model-value="fetchContent"
          >
            <template #chip="{ props, item }">
              <span class="mr-2">{{ $gettext('Display') }}</span>
              <v-chip
                v-bind="props"
                :color="item.raw.color"
                :text="item.raw.label"
                label
              ></v-chip>
            </template>
            <template #item="{ props, item }">
              <v-list-item v-bind="props" title="">
                <v-chip :color="item.raw.color" label>
                  {{ item.raw.label }}
                </v-chip>
              </v-list-item>
            </template>
          </v-select>
        </div>
      </template>
      <template #[`item.type`]="{ item }">
        <v-chip :color="getTypeColor(item.type)" size="small" label>
          {{ item.type }}
        </v-chip>
      </template>
      <template #[`item.status`]="{ item }">
        <v-icon
          v-if="item.status"
          :icon="getStatusIcon(item)"
          :title="getStatusTitle(item)"
          size="small"
        />
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
    <ConfirmDialog ref="learningRecipientRef">
      <v-radio-group v-model="learningDatabase" class="mt-4" hide-details>
        <v-radio
          v-for="lrcpt in learningRecipients"
          :key="lrcpt.value"
          :value="lrcpt.value"
          :label="lrcpt.title"
        >
        </v-radio>
      </v-radio-group>
    </ConfirmDialog>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute, useRouter } from 'vue-router'
import debounce from 'debounce'
import { useAuthStore, useBusStore } from '@/stores'
import { useAmavis } from '@/composables/amavis'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import api from '@/api/amavis'
import constants from '@/constants'

const { $gettext } = useGettext()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { displayNotification } = useBusStore()
const { manualLearningEnabled, learningRecipients } = await useAmavis()

const currentPage = ref(1)
const itemsPerPageR = ref(10)
const learningDatabase = ref(null)
const learningRecipientRef = ref(null)
const loading = ref(false)
const messages = ref([])
const search = ref('')
const searchCriteria = ref('both')
const selected = ref([])
const sortByR = ref([])
const totalMessages = ref(0)
const typeFilter = ref('all')

const messageTypes = [
  { color: '', key: 'all', label: 'All' },
  { color: 'success', key: 'C', label: 'Clean' },
  { color: 'error', key: 'S', label: 'Spam' },
  { color: 'warning', key: 'Y', label: 'Spammy' },
  { color: 'error', key: 'V', label: 'Virus' },
  { color: 'warning', key: 'H', label: 'Bad Header' },
  { color: 'warning', key: 'M', label: 'Bad MIME' },
  { color: 'warning', key: 'B', label: 'Banned' },
  { color: 'warning', key: 'O', label: 'Over sized' },
  { color: 'warning', key: 'T', label: 'MTA error' },
  { color: '', key: 'U', label: 'Unchecked' },
]

const headers = [
  { title: '', key: 'type', width: '5%' },
  { title: '', key: 'status', width: '5%' },
  { title: $gettext('Score'), key: 'score' },
  { title: $gettext('To'), key: 'to_address' },
  { title: $gettext('From'), key: 'from_address' },
  { title: $gettext('Subject'), key: 'subject' },
  { title: $gettext('Date'), key: 'datetime' },
]

watch(
  () => route.query.requests,
  () => {
    fetchContent()
  }
)

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

const getStatusIcon = (item) => {
  if (item.status === 'R') {
    return 'mdi-reply'
  }
  if (item.status === 'S') {
    return 'mdi-thumb-down-outline'
  }
  if (item.status === 'H') {
    return 'mdi-thumb-up-outline'
  }
  return ''
}

const getStatusTitle = (item) => {
  if (item.status === 'R') {
    return $gettext('Message released')
  }
  if (item.status === 'S') {
    return $gettext('Message marked as spam')
  }
  if (item.status === 'H') {
    return $gettext('Message marked as non-spam')
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
    params.criteria = searchCriteria.value
  }
  if (typeFilter.value !== 'all') {
    params.msgtype = typeFilter.value
  }
  if (route.query?.requests === '1') {
    params.viewrequests = 1
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
  if (
    manualLearningEnabled.value &&
    authStore.authUser.role !== constants.USER
  ) {
    learningDatabase.value =
      authStore.authUser.role === constants.SUPER_ADMIN ? 'global' : 'domain'
    await learningRecipientRef.value.open(
      $gettext('Learning database'),
      $gettext('Which database should be used for this learning:'),
      { width: 600, noconfirm: true }
    )
  }
  loading.value = true
  const data = prepareSelectionPayload()
  data.type = mtype
  if (learningDatabase.value) {
    data.database = learningDatabase.value
  }
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
</script>

<style lang="scss">
.unseen {
  font-weight: bold;
}
.clickable {
  cursor: pointer;
}
</style>
