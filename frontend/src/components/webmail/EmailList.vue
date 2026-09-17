<template>
  <div class="mail-toolbar mt-6 mb-2 mx-1">
    <v-checkbox
      v-model="selectAll"
      class="cell-check"
      color="primary"
      density="compact"
      hide-details
      :title="$gettext('Select every message of the page')"
      @update:model-value="toggleAllSelection"
    />

    <v-text-field
      v-model="search"
      prepend-inner-icon="mdi-magnify"
      :placeholder="$gettext('Search in messages')"
      class="mail-search"
      variant="solo-filled"
      single-line
      flat
      hide-details
      density="compact"
      clearable
      @click:clear="fetchEmails"
      @keyup.enter="submitSearch"
    ></v-text-field>

    <div class="mail-toolbar-group">
      <v-btn
        v-if="!inScheduledView"
        icon="mdi-trash-can-outline"
        color="error"
        variant="text"
        size="small"
        :loading="working"
        :title="$gettext('Delete')"
        @click="deleteSelection"
      />
      <template v-if="!inScheduledView">
        <v-btn
          v-if="!isJunkFolder"
          icon="mdi-fire"
          color="warning"
          variant="text"
          size="small"
          :loading="working"
          :title="$gettext('Mark as junk')"
          @click="markSelectionAsJunk"
        />
        <v-btn
          v-else
          icon="mdi-thumb-up-outline"
          color="success"
          variant="text"
          size="small"
          :loading="working"
          :title="$gettext('Mark as not junk')"
          @click="markSelectionAsNotJunk"
        />
      </template>
      <v-btn icon variant="text" size="small" :title="$gettext('More actions')">
        <v-icon icon="mdi-dots-horizontal" />
        <v-menu activator="parent">
          <v-list density="compact">
            <v-list-item
              :title="$gettext('Mark as read')"
              prepend-icon="mdi-eye"
              @click="() => flagSelection('read')"
            />
            <v-list-item
              :title="$gettext('Mark as unread')"
              prepend-icon="mdi-eye-outline"
              @click="() => flagSelection('unread')"
            />
            <v-list-item
              :title="$gettext('Mark as followed')"
              prepend-icon="mdi-star"
              @click="() => flagSelection('flagged')"
            />
            <v-list-item
              :title="$gettext('Mark as unfollowed')"
              prepend-icon="mdi-star-outline"
              @click="() => flagSelection('unflagged')"
            />
            <v-list-item
              v-if="isTrashFolder"
              :title="$gettext('Empty mailbox')"
              prepend-icon="mdi-trash-can"
              @click="emptyMailbox"
            />
          </v-list>
        </v-menu>
      </v-btn>
    </div>

    <template v-if="!inScheduledView">
      <span class="mail-toolbar-separator" />
      <v-btn-toggle
        :model-value="listingMode"
        class="mail-mode"
        density="compact"
        variant="text"
        mandatory
        @update:model-value="changeListingMode"
      >
        <v-btn
          value="flat"
          icon="mdi-format-list-bulleted"
          size="small"
          :title="$gettext('Display messages one by one')"
        />
        <v-btn
          value="threaded"
          icon="mdi-forum-outline"
          size="small"
          :disabled="!threadingAvailable"
          :title="threadingButtonTitle"
        />
      </v-btn-toggle>
    </template>

    <div class="mail-toolbar-spacer" />

    <div v-if="emails.results" class="mail-pagination">
      <span class="mail-range">
        {{ emails.first_index }}-{{ emails.last_index }} {{ $gettext('on') }}
        {{ emails.count }}
      </span>
      <v-btn
        icon="mdi-chevron-left"
        variant="text"
        size="small"
        :disabled="emails.prev_page === null"
        :title="$gettext('Previous page')"
        @click="page = emails.prev_page"
      />
      <v-btn
        icon="mdi-chevron-right"
        variant="text"
        size="small"
        :disabled="emails.next_page === null"
        :title="$gettext('Next page')"
        @click="page = emails.next_page"
      />
    </div>
  </div>
  <v-skeleton-loader v-if="loading" type="card@2"></v-skeleton-loader>
  <template v-else>
    <v-alert
      v-if="inScheduledView"
      type="info"
      variant="tonal"
      density="compact"
      class="mx-1"
    >
      {{
        $gettext(
          'Scheduled messages will be sent at the specified date and time. (visible on the right)'
        )
      }}
    </v-alert>
    <div
      class="emails position-absolute bottom-0 w-100 overflow-y-auto"
      :class="{ 'top-0': !inScheduledView, 'scheduling-top': inScheduledView }"
    >
      <div v-if="emails.results?.length" class="mail-list mx-1">
        <div class="mail-list-header">
          <span class="spacer-accent" />
          <span class="spacer-check" />
          <span class="spacer-icon" />
          <span v-if="displayThreads" class="spacer-expand" />
          <span class="cell-sender">
            {{ inScheduledView ? $gettext('Recipients') : $gettext('Sender') }}
          </span>
          <span class="cell-subject">{{ $gettext('Subject') }}</span>
          <span class="cell-date">{{ $gettext('Date') }}</span>
        </div>
        <template v-if="displayThreads">
          <ThreadListItem
            v-for="thread in emails.results"
            :key="thread.root"
            :thread="thread"
            :mailbox="props.mailbox"
            @open="openEmail"
            @open-thread="openThread"
            @toggle-follow="toggleFollowState"
            @dragstart="onDragStart"
          />
        </template>
        <template v-else>
          <EmailListItem
            v-for="email in emails.results"
            :key="email.imapid"
            :email="email"
            :scheduled="inScheduledView"
            @open="openEmail"
            @toggle-follow="toggleFollowState"
            @reschedule="reScheduleMessage"
            @delete-scheduled="deleteScheduledMessage"
            @scheduling-error="displaySchedulingError"
            @dragstart="onDragStart"
          />
        </template>
      </div>
      <v-alert
        v-else
        class="mt-4"
        type="info"
        :text="$gettext('No message yet in this mailbox')"
        variant="tonal"
      />
    </div>
    <v-dialog v-model="showSchedulingForm" max-width="800">
      <EmailSchedulingForm
        :initial-date="selectedScheduledEmail.scheduled_datetime_raw"
        @schedule="updateScheduledEmail"
        @close="closeSchedulingForm"
      />
    </v-dialog>
    <v-dialog v-model="showSchedulingError" max-width="400">
      <v-card
        max-width="400"
        :text="schedulingError"
        :title="$gettext('Sending failure')"
      >
        <template #:actions>
          <v-btn
            class="ms-auto"
            :text="$gettext('Close')"
            @click="showSchedulingError = false"
          ></v-btn>
        </template>
      </v-card>
    </v-dialog>
  </template>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useWebmailStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import EmailListItem from './EmailListItem.vue'
import EmailSchedulingForm from './EmailSchedulingForm.vue'
import ThreadListItem from './ThreadListItem.vue'
import api from '@/api/webmail'
import parametersApi from '@/api/parameters'

const props = defineProps({
  mailbox: {
    type: String,
    default: 'INBOX',
  },
})

const { $gettext, $ngettext } = useGettext()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const webmailStore = useWebmailStore()
const router = useRouter()
const route = useRoute()

const selectedScheduledEmail = ref(null)
const loading = ref(false)
const emails = ref({})
const page = ref(1)
const schedulingError = ref('')
const search = ref('')
const selectAll = ref(false)
const showSchedulingError = ref(false)
const showSchedulingForm = ref(false)
const working = ref(false)
// null until the server tells whether it supports the THREAD extension
const threadingSupported = ref(null)
// Whether the results currently held by `emails` are threads
const displayThreads = ref(false)
const userPreferences = ref(null)

let intervalId = null
let unmounted = false
// Which listing the last request asked for, to avoid fetching twice
let lastFetchWasThreaded = null
// Used when the refresh_interval preference can't be read
const DEFAULT_REFRESH_INTERVAL = 300

const currentMailbox = computed(() => {
  return route.query.mailbox || 'INBOX'
})

const inScheduledView = computed(() => props.mailbox === 'Scheduled')

const { isDraftsFolder, isJunkFolder, isTrashFolder } =
  useSpecialFolders(currentMailbox)

const listingMode = computed(() => webmailStore.listingMode)

// Conversations make no sense where messages have no reply chain, and
// the server may simply not support them
const threadingAvailable = computed(
  () =>
    !inScheduledView.value &&
    !isDraftsFolder.value &&
    threadingSupported.value !== false
)

const threadedMode = computed(
  () => listingMode.value === 'threaded' && threadingAvailable.value
)

const threadingButtonTitle = computed(() =>
  threadingAvailable.value
    ? $gettext('Group messages into conversations')
    : $gettext('Conversations are not available in this folder')
)

const changeListingMode = (mode) => {
  if (mode === listingMode.value) {
    return
  }
  webmailStore.setListingMode(mode)
  webmailStore.selection = []
  page.value = 1
  fetchEmails()
  saveListingMode(mode)
}

const saveListingMode = async (mode) => {
  if (!userPreferences.value) {
    return
  }
  try {
    await parametersApi.saveUserApplication('webmail', {
      ...userPreferences.value,
      listing_mode: mode,
    })
    userPreferences.value.listing_mode = mode
  } catch {
    // The mode still applies to this session
  }
}

const reScheduleMessage = (email) => {
  selectedScheduledEmail.value = email
  showSchedulingForm.value = true
}

const updateScheduledEmail = async (datetime) => {
  const data = {
    scheduled_datetime: datetime,
  }
  await api.updateScheduledMessage(
    selectedScheduledEmail.value.scheduled_id,
    data
  )
  fetchEmails()
  displayNotification({ msg: $gettext('Scheduling updated') })
}

const closeSchedulingForm = () => {
  showSchedulingForm.value = false
}

const deleteScheduledMessage = async (email) => {
  await api.deleteScheduledMessage(email.scheduled_id)
  fetchEmails()
  displayNotification({
    msg: $gettext('Scheduled canceled and message moved to trash folder'),
  })
}

const displaySchedulingError = async (email) => {
  const resp = await api.getScheduledMessage(email.scheduled_id)
  schedulingError.value = resp.data.error
  showSchedulingError.value = true
}

const openEmail = (emailid) => {
  router.push({
    name: 'EmailView',
    query: { mailbox: props.mailbox, mailid: emailid },
  })
}

const openThread = (mailid) => {
  router.push({
    name: 'ThreadView',
    query: { mailbox: props.mailbox, mailid },
  })
}

const fetchEmails = () => {
  emails.value = {}
  loading.value = true
  const options = { page: page.value, search: search.value }
  const threaded = threadedMode.value
  lastFetchWasThreaded = threaded
  const request = threaded
    ? api.getMailboxThreads(props.mailbox, options)
    : api.getMailboxEmails(props.mailbox, options)
  request
    .then((resp) => {
      if (resp.data.threading_supported !== undefined) {
        threadingSupported.value = resp.data.threading_supported
        if (!resp.data.threading_supported) {
          // The server can't thread: fall back to the flat listing
          fetchEmails()
          return
        }
      }
      // What is displayed follows the results, never the preference:
      // the mode can change before the matching request comes back,
      // and threads and messages don't carry the same fields
      displayThreads.value = threaded
      emails.value = resp.data
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

const autoRefreshContent = () => {
  fetchEmails()
  reloadMailboxCounters()
}

const submitSearch = () => {
  fetchEmails()
}

const toggleAllSelection = (value) => {
  if (!value) {
    webmailStore.selection = []
  } else if (displayThreads.value) {
    webmailStore.selection = emails.value.results.flatMap(
      (thread) => thread.uids
    )
  } else {
    webmailStore.selection = emails.value.results.map((email) => email.imapid)
  }
}

const deleteSelection = () => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  api.deleteSelection(currentMailbox.value, webmailStore.selection).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message(s) deleted') })
    fetchEmails()
    reloadMailboxCounters()
  })
}

const markSelectionAsJunk = () => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  api
    .markSelectionAsJunk(currentMailbox.value, webmailStore.selection)
    .then(() => {
      working.value = false
      displayNotification({ msg: $gettext('Message(s) marked as junk') })
      autoRefreshContent()
    })
}

const markSelectionAsNotJunk = () => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  api
    .markSelectionAsNotJunk(currentMailbox.value, webmailStore.selection)
    .then(() => {
      working.value = false
      displayNotification({ msg: $gettext('Message(s) marked as not junk') })
      autoRefreshContent()
    })
}

const flagSelection = (status) => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  api
    .flagSelection(currentMailbox.value, webmailStore.selection, status)
    .then(() => {
      working.value = false
      webmailStore.selection = []
      displayNotification({ msg: $gettext('Message(s) flagged') })
      fetchEmails()
      reloadMailboxCounters()
    })
}

const emptyMailbox = () => {
  loading.value = true
  api.emptyUserMailbox(currentMailbox.value).then(() => {
    emails.value = {}
    loading.value = false
    reloadMailboxCounters()
  })
}

const toggleFollowState = async (email) => {
  const flag = email.flagged ? 'unflagged' : 'flagged'
  await api.flagSelection(currentMailbox.value, [email.imapid], flag)
  email.flagged = flag === 'flagged'
}

// The event is passed explicitly: window.event doesn't exist in Firefox.
// ``ids`` holds one message, or every message of a conversation.
const onDragStart = (event, ids) => {
  if (!ids.some((id) => webmailStore.selection.includes(id))) {
    webmailStore.selection = [...ids]
  }
  const ghost = document.createElement('div')
  const count = webmailStore.selection.length || 0
  const msg = $ngettext('%{count} message', '%{count} messages', count, {
    count,
  })
  ghost.innerHTML = `
    <div class="pa-4 rounded-lg" style="background: #a9a9a9; opacity: 0.8; width: 300px">
      <div style="font-weight: 600">${msg}</div>
    </div>
  `
  document.body.appendChild(ghost)
  // Firefox doesn't start dragging when no data is set
  event.dataTransfer.setData('text/plain', webmailStore.selection.join(','))
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setDragImage(ghost, -10, -10)
  setTimeout(() => ghost.remove(), 0)
}

// Read the preferences the listing depends on: the refresh rate and the
// listing mode. Unset values are returned as null but refused on save,
// so they are dropped before keeping the payload for later updates.
const loadPreferences = async () => {
  try {
    const resp = await parametersApi.getUserApplication('webmail')
    const params = resp.data.params || {}
    userPreferences.value = Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== null)
    )
    if (!webmailStore.listingModeLoaded) {
      webmailStore.setListingMode(params.listing_mode)
    }
    const value = Number(params.refresh_interval)
    if (Number.isInteger(value) && value > 0) {
      return value
    }
  } catch {
    // Keep refreshing with the default interval
  }
  return DEFAULT_REFRESH_INTERVAL
}

onMounted(async () => {
  if (webmailStore.listingModeLoaded) {
    // The mode is known from a previous listing: don't wait
    fetchEmails()
  }
  const interval = await loadPreferences()
  if (unmounted) {
    return
  }
  if (threadedMode.value !== lastFetchWasThreaded) {
    fetchEmails()
  }
  intervalId = setInterval(autoRefreshContent, interval * 1000)
})

onUnmounted(() => {
  unmounted = true
  clearInterval(intervalId)
})

watch(
  () => props.mailbox,
  () => {
    fetchEmails()
  }
)
watch(
  () => webmailStore.selection,
  () => {
    if (!webmailStore.selection.length) {
      selectAll.value = false
    } else {
      selectAll.value = true
    }
  }
)
watch(
  () => webmailStore.listingKey,
  () => {
    fetchEmails()
  }
)
watch(page, () => {
  fetchEmails()
})
</script>

<style lang="scss" scoped>
.emails {
  margin-top: 150px;
}
.scheduling-top {
  top: 45px;
}
</style>
