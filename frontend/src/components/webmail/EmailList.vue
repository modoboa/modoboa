<template>
  <div class="email-list-wrapper">
    <v-card class="email-toolbar-card">
      <!-- Contextual toolbar (Gmail-style): browsing state shows the search
           and passive controls; the moment something is selected it swaps to
           the bulk actions. The two never compete for width, so the bar fits
           any pane width (wrapping is driven by @container, not viewport). -->
      <v-toolbar class="email-toolbar">
        <v-checkbox
          v-model="selectAll"
          class="select-all"
          density="compact"
          hide-details
          color="primary"
          :aria-label="$gettext('Select all messages')"
          @update:model-value="toggleAllSelection"
        />

        <template v-if="!hasSelection">
          <v-text-field
            ref="searchField"
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            :placeholder="$gettext('Search in messages')"
            :aria-label="$gettext('Search in messages')"
            variant="outlined"
            single-line
            flat
            hide-details
            density="compact"
            class="search-field"
            clearable
            @click:clear="submitSearch"
            @keyup.enter="submitSearch"
          ></v-text-field>
          <v-btn
            v-if="!inScheduledView"
            class="tb-btn"
            variant="text"
            icon="mdi-pencil"
            size="small"
            :title="$gettext('Compose')"
            :aria-label="$gettext('Compose')"
            @click="openComposeForm"
          >
          </v-btn>
          <v-btn
            class="tb-btn"
            variant="text"
            icon="mdi-refresh"
            size="small"
            :loading="loadingMore"
            :title="$gettext('Refresh')"
            :aria-label="$gettext('Refresh')"
            @click="reloadListing"
          >
          </v-btn>
          <v-btn
            v-if="currentMailbox === 'Trash'"
            class="tb-btn"
            variant="text"
            icon
            size="small"
            :title="$gettext('More actions')"
            :aria-label="$gettext('More actions')"
          >
            <v-icon icon="mdi-cog" />
            <v-menu activator="parent">
              <v-list density="compact">
                <v-list-item
                  :title="$gettext('Empty mailbox')"
                  prepend-icon="mdi-trash-can"
                  @click="emptyMailbox"
                />
              </v-list>
            </v-menu>
          </v-btn>
          <v-spacer />
          <div
            class="count-nav"
            :title="$gettext('Loaded / total messages')"
          >
            {{ store.emails.length }}/{{ store.emailCount }}
          </div>
        </template>

        <template v-else>
          <span class="selection-label">{{ selectionLabel }}</span>
          <v-spacer />
          <v-btn
            v-if="!inScheduledView"
            class="ml-1"
            color="error"
            variant="tonal"
            icon="mdi-trash-can"
            size="small"
            :title="$gettext('Delete selection')"
            :aria-label="$gettext('Delete selection')"
            :loading="working"
            @click="deleteSelection"
          >
          </v-btn>
          <template v-if="!inScheduledView">
            <v-btn
              v-if="currentMailbox === 'Trash'"
              class="ml-1"
              color="primary"
              variant="tonal"
              icon="mdi-backup-restore"
              size="small"
              :title="$gettext('Restore to Inbox')"
              :aria-label="$gettext('Restore to Inbox')"
              :loading="working"
              @click="restoreSelection"
            >
            </v-btn>
            <v-btn
              v-else-if="currentMailbox === 'Junk'"
              class="ml-1"
              color="success"
              variant="tonal"
              icon="mdi-thumb-up"
              size="small"
              :title="$gettext('Mark selection as not junk')"
              :aria-label="$gettext('Mark selection as not junk')"
              :loading="working"
              @click="markSelectionAsNotJunk"
            >
            </v-btn>
            <v-btn
              v-else
              class="ml-1"
              color="warning"
              variant="tonal"
              icon="mdi-alert-octagon-outline"
              size="small"
              :title="$gettext('Mark selection as junk')"
              :aria-label="$gettext('Mark selection as junk')"
              :loading="working"
              @click="markSelectionAsJunk"
            >
            </v-btn>
          </template>
          <v-btn
            class="ml-1"
            variant="tonal"
            icon
            size="small"
            :title="$gettext('More actions')"
            :aria-label="$gettext('More actions')"
          >
            <v-icon icon="mdi-dots-vertical" />
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
              </v-list>
            </v-menu>
          </v-btn>
          <v-btn
            class="ml-1"
            variant="text"
            icon="mdi-close"
            size="small"
            :title="$gettext('Clear selection')"
            :aria-label="$gettext('Clear selection')"
            @click="clearSelection"
          >
          </v-btn>
        </template>
      </v-toolbar>
    </v-card>
    <div class="emails-content">
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
      <div ref="scroller" class="emails" @scroll="onScroll">
        <div
          v-show="pullPx > 0 || refreshing"
          class="emails__ptr"
          :style="{ transform: `translateY(${pullPx}px)` }"
        >
          <v-progress-circular
            :indeterminate="refreshing"
            :model-value="Math.min(100, (pullPx / 70) * 100)"
            size="24"
            width="2"
            color="primary"
          />
        </div>
        <template v-if="store.emails.length">
          <div class="email-list">
            <SwipeableRow
              v-for="(email, index) in store.emails"
              :key="email.imapid"
              :enabled="!inScheduledView"
              :left-action="{
                icon: 'mdi-trash-can',
                color: 'error',
                label: $gettext('Delete'),
              }"
              :right-action="{
                icon:
                  email.style === 'unseen'
                    ? 'mdi-email-open-outline'
                    : 'mdi-email-outline',
                color: 'primary',
                label:
                  email.style === 'unseen'
                    ? $gettext('Read')
                    : $gettext('Unread'),
              }"
              @swipe-left="swipeDelete(email, index)"
              @swipe-right="swipeToggleRead(email)"
            >
              <div
                class="email-row"
                :class="{
                  'email-row--unseen': email.style === 'unseen',
                  'email-row--active': email.imapid === activeMailid,
                  'email-row--focus': index === activeIndex,
                }"
                draggable="true"
                @dragstart="onDragStart(email)"
              >
                <div class="email-row__actions">
                  <v-checkbox
                    v-model="webmailStore.selection"
                    :value="email.imapid"
                    color="primary"
                    density="compact"
                    hide-details
                    :aria-label="
                      $gettext('Select message: %{subject}', {
                        subject: email.subject,
                      })
                    "
                  />
                  <v-btn
                    :icon="email.flagged ? 'mdi-star' : 'mdi-star-outline'"
                    :color="email.flagged ? 'warning' : undefined"
                    variant="text"
                    size="small"
                    class="email-row__star"
                    :title="
                      email.flagged
                        ? $gettext('Unfollow message')
                        : $gettext('Follow message')
                    "
                    :aria-label="
                      email.flagged
                        ? $gettext('Unfollow message')
                        : $gettext('Follow message')
                    "
                    @click="toggleFollowState(email)"
                  />
                  <v-menu v-if="inScheduledView" location="bottom">
                    <template #activator="{ props }">
                      <v-btn
                        icon="mdi-dots-vertical"
                        v-bind="props"
                        size="small"
                        variant="text"
                        :aria-label="$gettext('Message actions')"
                      >
                      </v-btn>
                    </template>
                    <MenuItems
                      :items="getScheduledMessageActions()"
                      :obj="email"
                    />
                  </v-menu>
                </div>

                <div class="email-row__content">
                  <div
                    class="email-row__main clickable"
                    @click="openEmail(email.imapid)"
                  >
                    <div class="email-row__subject">{{ email.subject }}</div>
                    <div class="email-row__from">
                      <EmailAddressList :addresses="getEmailAddresses(email)" />
                    </div>
                  </div>

                  <div class="email-row__meta">
                    <div
                      v-if="!isScheduledDateOver(email)"
                      class="email-row__date"
                    >
                      {{ getEmailDate(email) }}
                    </div>
                    <div
                      v-else
                      class="email-row__date email-row__date--error clickable"
                      @click="displaySchedulingError(email)"
                    >
                      {{ getEmailDate(email) }}
                    </div>
                    <div class="email-row__flags">
                      <v-icon
                        v-if="email.answered"
                        icon="mdi-reply-outline"
                        size="small"
                      />
                      <v-icon
                        v-if="email.forwarded"
                        icon="mdi-share-outline"
                        size="small"
                      />
                      <v-icon
                        v-if="email.attachments"
                        icon="mdi-paperclip"
                        size="small"
                      />
                      <span>{{ $filesize(email.size) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </SwipeableRow>
          </div>
        </template>
        <EmptyState
          v-else-if="showEmpty && search"
          icon="mdi-magnify"
          :eyebrow="$gettext('Search')"
          :title="$gettext('No messages match your search')"
          :message="
            $gettext(
              'Try a different term or clear the search to see all messages.'
            )
          "
        />
        <EmptyState
          v-else-if="showEmpty"
          icon="mdi-inbox"
          :eyebrow="$gettext('Mailbox')"
          :title="$gettext('This mailbox is empty')"
          :message="$gettext('New messages will appear here.')"
        />
        <div v-if="loadingMore" class="emails__loader">
          <v-progress-circular
            indeterminate
            size="20"
            width="2"
            color="primary"
          />
        </div>
      </div>
      <v-dialog
        v-model="showSchedulingForm"
        :fullscreen="mobile"
        :max-width="mobile ? undefined : 800"
        :transition="mobile ? 'dialog-bottom-transition' : undefined"
      >
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
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useWebmailStore } from '@/stores'
import { DateTime } from 'luxon'
import EmailAddressList from './EmailAddressList.vue'
import EmailSchedulingForm from './EmailSchedulingForm.vue'
import EmptyState from '@/components/tools/EmptyState.vue'
import SwipeableRow from './SwipeableRow.vue'
import MenuItems from '@/components/tools/MenuItems.vue'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import api from '@/api/webmail'

const props = defineProps({
  mailbox: {
    type: String,
    default: 'INBOX',
  },
  // imapid of the message currently open in the reading pane (desktop split
  // view); highlights the matching row.
  activeMailid: {
    type: String,
    default: null,
  },
})

// 'active-deleted': the message currently open in the reading pane was just
// deleted from the list side — the host should clear the pane.
const emit = defineEmits(['open-email', 'active-deleted'])

const { $gettext, $ngettext } = useGettext()
const { mobile } = useDisplay()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const webmailStore = useWebmailStore()
const store = webmailStore
const router = useRouter()
const route = useRoute()

const selectedScheduledEmail = ref(null)
const scroller = ref(null)
const loadingMore = ref(false)
// Deferred swipe-deletes awaiting their Undo window: { imapid, row, index,
// timer }. The server call is delayed so Undo needs no reverse-move (which
// would be unreliable — IMAP re-keys UIDs on move).
const pendingDeletes = ref([])
const schedulingError = ref('')
const search = ref('')
const selectAll = ref(false)
const showSchedulingError = ref(false)
const showSchedulingForm = ref(false)
const working = ref(false)

// Empty state only once the first load settled with nothing to show.
const showEmpty = computed(
  () => store.emails.length === 0 && store.nextPage === null
)

// Contextual toolbar: with a selection the search gives way to the bulk
// actions (Gmail pattern).
const hasSelection = computed(() => webmailStore.selection.length > 0)

const selectionLabel = computed(() =>
  $ngettext(
    '%{ count } selected',
    '%{ count } selected',
    webmailStore.selection.length,
    { count: webmailStore.selection.length }
  )
)

const clearSelection = () => {
  webmailStore.selection = []
}

let intervalId = null

const currentMailbox = computed(() => {
  return route.query.mailbox || 'INBOX'
})

const openComposeForm = () => {
  router.push({ name: 'ComposeEmailView' })
}

const inScheduledView = computed(() => props.mailbox === 'Scheduled')

const getScheduledMessageActions = () => {
  return [
    {
      label: $gettext('Reschedule'),
      icon: 'mdi-send-clock-outline',
      onClick: reScheduleMessage,
    },
    {
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteScheduledMessage,
      color: 'red',
    },
  ]
}

const getEmailAddresses = (email) => {
  if (inScheduledView.value) {
    return email.recipients
  }
  return [email.from_address]
}

const getEmailDate = (email) => {
  if (inScheduledView.value) {
    return email.scheduled_datetime
  }
  return email.date
}

const isScheduledDateOver = (email) => {
  if (!inScheduledView.value || !email.scheduled_datetime_raw) return false
  const date = DateTime.fromISO(email.scheduled_datetime_raw)
  return date < DateTime.now()
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
  reloadListing()
  displayNotification({ msg: $gettext('Scheduling updated') })
}

const closeSchedulingForm = () => {
  showSchedulingForm.value = false
}

const deleteScheduledMessage = async (email) => {
  await api.deleteScheduledMessage(email.scheduled_id)
  reloadListing()
  displayNotification({
    msg: $gettext('Scheduled canceled and message moved to trash folder'),
  })
}

const displaySchedulingError = async (email) => {
  const resp = await api.getScheduledMessage(email.scheduled_id)
  schedulingError.value = resp.data.error
  showSchedulingError.value = true
}

const saveScroll = () => {
  if (scroller.value) {
    store.listScrollTop = scroller.value.scrollTop
  }
}

const openEmail = (emailid) => {
  saveScroll()
  // Keep the keyboard cursor in sync with mouse opens so j/k continues from
  // the message the user actually read.
  activeIndex.value = store.emails.findIndex((e) => e.imapid === emailid)
  emit('open-email', emailid)
}

// ----- keyboard navigation (driven by MailboxView's shortcuts) -----
// Index of the row the keyboard cursor sits on; -1 = none.
const activeIndex = ref(-1)
const searchField = ref(null)

const scrollActiveIntoView = () => {
  const rows = scroller.value?.querySelectorAll('.email-row')
  rows?.[activeIndex.value]?.scrollIntoView({ block: 'nearest' })
}

const moveActive = (delta) => {
  if (!store.emails.length) {
    return
  }
  const next =
    activeIndex.value === -1
      ? 0
      : Math.min(
          Math.max(activeIndex.value + delta, 0),
          store.emails.length - 1
        )
  activeIndex.value = next
  scrollActiveIntoView()
  // Keep j flowing past the loaded pages.
  if (next >= store.emails.length - 3) {
    loadMore()
  }
  // With a message open in the reading pane, j/k means next/previous message
  // (Outlook-style); with no message open it only moves the highlight.
  if (props.activeMailid) {
    openEmail(store.emails[next].imapid)
  }
}

const openActive = () => {
  const row = store.emails[activeIndex.value]
  if (row) {
    openEmail(row.imapid)
  }
}

const toggleActiveSelection = () => {
  const row = store.emails[activeIndex.value]
  if (!row) {
    return
  }
  const i = webmailStore.selection.indexOf(row.imapid)
  if (i === -1) {
    webmailStore.selection = [...webmailStore.selection, row.imapid]
  } else {
    webmailStore.selection = webmailStore.selection.filter(
      (id) => id !== row.imapid
    )
  }
}

const deleteActiveOrSelection = () => {
  if (webmailStore.selection.length) {
    deleteSelection()
    return
  }
  const row = store.emails[activeIndex.value]
  if (row) {
    // Same optimistic delete + Undo snackbar as swipe.
    swipeDelete(row)
    activeIndex.value = Math.min(activeIndex.value, store.emails.length - 1)
  }
}

const focusSearch = () => {
  // The search field only exists in the browsing state of the contextual
  // toolbar: drop any selection first, then focus once it rendered.
  webmailStore.selection = []
  nextTick(() => searchField.value?.focus())
}

defineExpose({
  moveActive,
  openActive,
  toggleActiveSelection,
  deleteActiveOrSelection,
  focusSearch,
})

// ----- swipe gestures (touch) -----
const commitDelete = (entry) => {
  const i = pendingDeletes.value.indexOf(entry)
  if (i === -1) {
    return
  }
  pendingDeletes.value.splice(i, 1)
  clearTimeout(entry.timer)
  api.deleteSelection(currentMailbox.value, [entry.imapid]).then(() => {
    reloadMailboxCounters()
  })
}

const undoDelete = (entry) => {
  const i = pendingDeletes.value.indexOf(entry)
  if (i === -1) {
    return
  }
  pendingDeletes.value.splice(i, 1)
  clearTimeout(entry.timer)
  // Server was never told to delete (deferred), so just put the row back.
  store.restoreEmails([entry.row], Math.min(entry.index, store.emails.length))
}

const swipeDelete = (email) => {
  const index = store.emails.findIndex((e) => e.imapid === email.imapid)
  if (index === -1) {
    return
  }
  const entry = { imapid: email.imapid, row: email, index }
  store.removeEmails([email.imapid])
  entry.timer = setTimeout(() => commitDelete(entry), 5000)
  pendingDeletes.value.push(entry)
  if (props.activeMailid === email.imapid) {
    // The message being read was just deleted from the list: clear the pane
    // (replying to a deleted message would 404).
    emit('active-deleted')
  }
  displayNotification({
    msg: $gettext('Message deleted'),
    timeout: 5000,
    action: { label: $gettext('Undo'), handler: () => undoDelete(entry) },
  })
}

const swipeToggleRead = (email) => {
  const status = email.style === 'unseen' ? 'read' : 'unread'
  store.patchEmail(email.imapid, { style: status === 'read' ? '' : 'unseen' })
  api
    .flagSelection(currentMailbox.value, [email.imapid], status)
    .then(() => reloadMailboxCounters())
}

// ----- pull to refresh (touch) -----
const refreshListing = async () => {
  store.resetListing(props.mailbox, search.value)
  await loadMore()
}

const { pullPx, refreshing } = usePullToRefresh(scroller, {
  onRefresh: refreshListing,
})

// Fetch the next page and append it. Guarded so only one request is in flight;
// after appending, if the list still doesn't overflow the viewport, keep
// loading until it does or the mailbox is exhausted (initial viewport fill).
const loadMore = async () => {
  if (loadingMore.value || store.nextPage === null) {
    return
  }
  loadingMore.value = true
  try {
    const resp = await api.getMailboxEmails(props.mailbox, {
      page: store.nextPage,
      search: search.value,
    })
    store.appendPage(resp.data)
  } finally {
    loadingMore.value = false
  }
  await nextTick()
  const el = scroller.value
  if (el && store.nextPage !== null && el.scrollHeight <= el.clientHeight) {
    loadMore()
  }
}

// Load the next page as the user nears the bottom (300px lookahead).
const onScroll = () => {
  const el = scroller.value
  if (!el) {
    return
  }
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 300) {
    loadMore()
  }
}

// Reset accumulated pages then fetch page 1.
const reloadListing = () => {
  if (!search.value) {
    search.value = ''
  }
  store.resetListing(props.mailbox, search.value)
  activeIndex.value = -1
  nextTick(() => {
    if (scroller.value) {
      scroller.value.scrollTop = 0
    }
    loadMore()
  })
}

// Restore a saved scroll position once the rows have actually laid out.
// Setting scrollTop too early clamps it to a still-growing scrollHeight, so
// retry across a few frames until the target is reachable (or we give up).
const restoreScroll = (target, tries = 40) => {
  const el = scroller.value
  if (!el || target <= 0) {
    return
  }
  el.scrollTop = target
  // Keep retrying until the target is reachable: the route's out-in
  // transition means the rows may still be settling their height for a few
  // hundred ms after mount, which would clamp an early scrollTop.
  if (Math.abs(el.scrollTop - target) > 1 && tries > 0) {
    requestAnimationFrame(() => restoreScroll(target, tries - 1))
  }
}

// Called on mount and mailbox change: restore the cached pages + scroll
// position when still fresh (back from the reading view on mobile), else
// start over from page 1.
const initListing = () => {
  if (store.isListingFresh(props.mailbox, search.value)) {
    const target = store.listScrollTop
    nextTick(() => restoreScroll(target))
  } else {
    reloadListing()
  }
}

const autoRefreshContent = () => {
  // Don't yank the user's position: only refresh when the tab is visible and
  // they're near the top of the list.
  if (document.visibilityState !== 'visible') {
    return
  }
  if (scroller.value && scroller.value.scrollTop > 200) {
    return
  }
  reloadListing()
}

const submitSearch = () => {
  reloadListing()
}

const toggleAllSelection = (value) => {
  if (!value) {
    webmailStore.selection = []
  } else {
    webmailStore.selection = store.emails.map((email) => email.imapid)
  }
}

const deleteSelection = () => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  const deletesActive = webmailStore.selection.includes(props.activeMailid)
  api.deleteSelection(currentMailbox.value, webmailStore.selection).then(() => {
    working.value = false
    webmailStore.selection = []
    displayNotification({ msg: $gettext('Message(s) deleted') })
    if (deletesActive) {
      emit('active-deleted')
    }
    reloadListing()
    reloadMailboxCounters()
  })
}

const restoreSelection = () => {
  if (!webmailStore.selection.length) {
    return
  }
  working.value = true
  api
    .moveSelection(currentMailbox.value, 'INBOX', webmailStore.selection)
    .then(() => {
      working.value = false
      webmailStore.selection = []
      displayNotification({ msg: $gettext('Message(s) restored to Inbox') })
      reloadListing()
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
      webmailStore.selection = []
      displayNotification({ msg: $gettext('Message(s) marked as junk') })
      reloadListing()
      reloadMailboxCounters()
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
      webmailStore.selection = []
      displayNotification({ msg: $gettext('Message(s) marked as not junk') })
      reloadListing()
      reloadMailboxCounters()
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
      reloadListing()
      reloadMailboxCounters()
    })
}

const emptyMailbox = () => {
  api.emptyUserMailbox(currentMailbox.value).then(() => {
    reloadListing()
    reloadMailboxCounters()
  })
}

const toggleFollowState = async (email) => {
  const flag = email.flagged ? 'unflagged' : 'flagged'
  await api.flagSelection(currentMailbox.value, [email.imapid], flag)
  email.flagged = flag === 'flagged'
}

const onDragStart = (email) => {
  if (!webmailStore.selection.includes(email.imapid)) {
    webmailStore.selection = [email.imapid]
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
  event.dataTransfer.setDragImage(ghost, -10, -10)
  setTimeout(() => ghost.remove(), 0)
}

onMounted(() => {
  initListing()
  intervalId = setInterval(autoRefreshContent, 300 * 1000)
})

onUnmounted(() => {
  // Note: the scroll position is saved in openEmail() at click time, not
  // here — during route navigation the container can be scrolled/reset before
  // unmount, which would overwrite the position the user actually left from.
  clearInterval(intervalId)
  // Flush any pending swipe-deletes so leaving the view still deletes them.
  pendingDeletes.value.slice().forEach(commitDelete)
})

watch(
  () => props.mailbox,
  () => {
    // Mailbox switch always starts fresh (also clears search + selection).
    search.value = ''
    reloadListing()
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
    reloadListing()
  }
)
</script>

<style lang="scss" scoped>
/* Flex column so the message list takes the remaining height and scrolls
   internally. Replaces the old absolute positioning + magic margin-top:150px,
   which broke when the toolbar wrapped to several rows on narrow screens. */
.email-list-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  /* Size container: the toolbar adapts to the width of THIS pane (split
     view can be ~400px on a 1920px screen), not the viewport. */
  container-type: inline-size;
}
.email-toolbar-card {
  flex: 0 0 auto;
  margin: 1.5rem 0.25rem 0.5rem;
}

/* --- Contextual toolbar --- */
.email-toolbar :deep(.v-toolbar__content) {
  height: auto !important;
  min-height: 48px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  row-gap: 6px;
  padding: 6px 10px;
}
/* Browsing state: the search takes all the free width between the select-all
   checkbox and the passive action buttons. */
.email-toolbar :deep(.search-field) {
  flex: 1 1 auto;
  min-width: 140px;
  max-width: 520px;
  margin-right: 8px;
}
.select-all {
  flex: 0 0 auto;
  margin-right: 4px;
}
/* Passive buttons stay quiet (dim, no fill); color belongs to the transient
   selection actions. */
.tb-btn {
  color: var(--fg-dim);
}
.count-nav {
  margin-left: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--fg-mute);
  white-space: nowrap;
}
.selection-label {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.04em;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* Narrow pane/screen: search gets its own full-width row below the buttons
   (order pushes it after everything else). Falls back to the single wrapping
   row on engines without container queries. */
@container (max-width: 480px) {
  .email-toolbar :deep(.search-field) {
    order: 10;
    flex: 1 1 100%;
    max-width: none;
    margin-right: 0;
  }
}
.emails-content {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.emails {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior-y: contain;
}
.emails__loader {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
/* Pull-to-refresh indicator: pinned just above the list, pushed down by the
   pull distance. */
.emails__ptr {
  position: absolute;
  top: -36px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
}
.clickable {
  cursor: pointer;
}

/* Dense hairline message list (portfolio editorial rows). */
.email-list {
  margin: 0 4px 8px;
  border: 1px solid var(--line-2);
  border-radius: 0;
  background: var(--bg);
  overflow: hidden;
}
.email-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 16px 6px 6px;
  border-bottom: 1px solid var(--line);
  transition: background 0.2s;
}
.email-row:last-child {
  border-bottom: 0;
}
.email-row:hover {
  background: var(--bg-2);
}
.email-row--unseen::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--accent);
}
/* Keyboard cursor (j/k): inset hairline ring, distinct from the opened-row
   background highlight. */
.email-row--focus {
  outline: 1px solid var(--accent);
  outline-offset: -1px;
}
/* Row open in the reading pane (desktop split view). */
.email-row--active {
  background: rgba(124, 92, 255, 0.12);
  box-shadow: inset 2px 0 0 var(--accent);
}
.email-row--active:hover {
  background: rgba(124, 92, 255, 0.16);
}
.email-row__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 0 0 auto;
}
.email-row__content {
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  margin-left: 8px;
}
.email-row__main {
  flex: 1 1 auto;
  min-width: 0;
}
.email-row__subject {
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(13px, 2vw, 15px);
  letter-spacing: -0.01em;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.email-row--unseen .email-row__subject {
  font-weight: 700;
}
.email-row__from {
  margin-top: 2px;
  font-family: var(--font-mono);
  font-size: clamp(11px, 1.5vw, 12px);
  letter-spacing: 0.02em;
  color: var(--fg-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.email-row__meta {
  flex: 0 0 auto;
  padding-left: 16px;
  text-align: right;
}
.email-row__date {
  font-family: var(--font-mono);
  font-size: clamp(9px, 1.2vw, 10.5px);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--fg-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.email-row__date--error {
  color: rgb(var(--v-theme-error));
  font-weight: 700;
}
.email-row__flags {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: clamp(9px, 1.2vw, 10.5px);
  color: var(--fg-mute);
}

/* Touch-size adjustments on phones (the toolbar LAYOUT itself is handled by
   the container query above, since it depends on pane width, not viewport). */
@media (max-width: 700px) {
  /* --- Message rows: optimise for reading on a narrow screen. --- */
  /* The per-row follow star is desktop chrome; drop it on mobile to give the
     subject/sender the full width (follow stays in the reading view + the
     toolbar's "mark as followed" menu). */
  .email-row__star {
    display: none;
  }
  .email-row {
    /* Taller rows = comfortable tap targets (WCAG 2.5.8). */
    padding: 10px 12px 10px 8px;
    align-items: center;
    min-height: 56px;
  }
  .email-row :deep(.v-input__control) {
    display: flex;
    align-items: center;
  }
  /* Row checkbox: a full 44px hit area, not just the 24px glyph. */
  .email-row__actions :deep(.v-selection-control) {
    min-width: 44px;
    min-height: 44px;
    justify-content: center;
  }
  /* Toolbar action buttons reach the 44px minimum too. */
  .email-toolbar :deep(.v-btn) {
    min-width: 44px;
    min-height: 44px;
  }
  .email-row__actions {
    display: flex;
    align-items: center;
    gap: 2px;
    flex: 0 0 auto;
  }
  .email-row__content {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    flex: 1 1 auto;
    min-width: 0;
    margin-left: 4px;
  }
  .email-row__main {
    margin-left: 0;
  }

  .email-row__meta {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding-left: 0;
    flex-basis: auto;
    margin-top: 4px;
  }
  .email-row__date {
    letter-spacing: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1 1 auto;
    min-width: 0;
    margin-right: 8px;
    /* Readable floor on small screens (9px was too small). */
    font-size: 11px;
  }
  .email-row__flags {
    margin-top: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
  }
  .email-row__flags :deep(.v-icon) {
    font-size: 12px;
  }
}
</style>
