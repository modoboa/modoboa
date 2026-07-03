<template>
  <div class="mailbox-view d-flex flex-column h-100">
    <div class="d-flex align-center ml-4">
      <span class="text-headline-medium">{{ currentFolderLabel }}</span>
      <v-btn
        icon
        variant="text"
        size="small"
        class="ml-2"
        :title="$gettext('Mailbox settings')"
        :aria-label="$gettext('Mailbox settings')"
      >
        <v-icon icon="mdi-cog-outline" />
        <v-menu activator="parent" location="bottom">
          <v-list density="compact">
            <v-list-item
              :title="$gettext('Create a new mailbox')"
              prepend-icon="mdi-plus"
              @click="openMailboxForm"
            />
            <v-list-item
              :title="$gettext('Edit this mailbox')"
              prepend-icon="mdi-pencil"
              :disabled="readOnlyMailbox"
              @click="editMailbox"
            />
            <v-list-item
              :title="$gettext('Delete this mailbox')"
              prepend-icon="mdi-trash-can"
              :disabled="readOnlyMailbox"
              @click="deleteMailbox"
            />
            <v-list-item
              :title="$gettext('Compress this mailbox')"
              prepend-icon="mdi-folder-zip-outline"
              @click="compressMailbox"
            />
          </v-list>
        </v-menu>
      </v-btn>
    </div>
    <!-- Desktop: list on the left, reading pane on the right (Outlook-style),
         driven by the ?mailid= query so URLs stay shareable and back/forward
         walks through opened messages. Mobile keeps the single-column flow
         (list here, message on the EmailView route). -->
    <div v-if="!mobile" ref="splitRef" class="mailbox-split">
      <div class="mailbox-split__list" :style="{ width: listPaneWidth + 'px' }">
        <EmailList
          ref="listRef"
          :mailbox="currentMailbox"
          :active-mailid="openedMailid"
          @open-email="onOpenEmail"
          @active-deleted="clearOpenedMail"
        />
      </div>
      <div
        class="mailbox-split__divider"
        :class="{ 'is-dragging': paneResizing }"
        role="separator"
        aria-orientation="vertical"
        :aria-label="$gettext('Resize reading pane')"
        tabindex="0"
        @pointerdown="startPaneResize"
        @keydown="onDividerKeydown"
      />
      <div class="mailbox-split__pane">
        <EmailContent
          v-if="openedMailid"
          :mailbox="currentMailbox"
          :mailid="openedMailid"
          :show-back-button="false"
          @deleted="onPaneDeleted"
          @loaded="onPaneLoaded"
        />
        <EmptyState
          v-else
          icon="mdi-email"
          :eyebrow="$gettext('Reading pane')"
          :title="$gettext('No message selected')"
          :message="$gettext('Pick a message from the list to read it here.')"
        />
      </div>
    </div>
    <EmailList
      v-else
      :mailbox="currentMailbox"
      @open-email="onOpenEmail"
    />

    <v-dialog
      v-model="showMailboxForm"
      :fullscreen="mobile"
      :max-width="mobile ? undefined : 800"
      :transition="mobile ? 'dialog-bottom-transition' : undefined"
    >
      <MailboxForm
        :user-mailboxes="userMailboxes"
        :mailbox="editedMailbox"
        :hdelimiter="hdelimiter"
        @mailbox-renamed="navigateToMailbox"
        @close="closeMailboxForm()"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" />
    <ShortcutHelpDialog v-model="showShortcutHelp" :bindings="shortcuts" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useWebmailStore } from '@/stores'
import EmailList from '@/components/webmail/EmailList.vue'
import EmailContent from '@/components/webmail/EmailContent.vue'
import MailboxForm from '@/components/webmail/MailboxForm.vue'
import ShortcutHelpDialog from '@/components/webmail/ShortcutHelpDialog.vue'
import EmptyState from '@/components/tools/EmptyState.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import api from '@/api/webmail'

const { $gettext } = useGettext()
const { mobile } = useDisplay()
const route = useRoute()
const router = useRouter()
const busStore = useBusStore()
const webmailStore = useWebmailStore()

const confirm = ref()
const listRef = ref(null)
const userMailboxes = ref([])
const hdelimiter = ref(null)
const editedMailbox = ref(null)
const showMailboxForm = ref(false)
const showShortcutHelp = ref(false)

const currentMailbox = computed(() => route.query.mailbox || 'INBOX')
const openedMailid = computed(() => route.query.mailid || null)

// ----- keyboard shortcuts (desktop only) -----
const shortcuts = useKeyboardShortcuts(
  [
    {
      keys: ['c'],
      description: $gettext('Compose a new message'),
      handler: () => router.push({ name: 'ComposeEmailView' }),
    },
    {
      keys: ['/'],
      description: $gettext('Focus the search field'),
      handler: () => listRef.value?.focusSearch(),
    },
    {
      keys: ['j'],
      description: $gettext('Next message'),
      handler: () => listRef.value?.moveActive(1),
    },
    {
      keys: ['k'],
      description: $gettext('Previous message'),
      handler: () => listRef.value?.moveActive(-1),
    },
    {
      keys: ['Enter', 'o'],
      description: $gettext('Open the highlighted message'),
      handler: () => listRef.value?.openActive(),
    },
    {
      keys: ['x'],
      description: $gettext('Select/unselect the highlighted message'),
      handler: () => listRef.value?.toggleActiveSelection(),
    },
    {
      keys: ['#', 'Delete'],
      description: $gettext('Delete the selection or highlighted message'),
      handler: () => listRef.value?.deleteActiveOrSelection(),
    },
    {
      keys: ['r'],
      description: $gettext('Reply to the open message'),
      handler: () => {
        if (openedMailid.value) {
          router.push({
            name: 'ReplyEmailView',
            query: { mailbox: currentMailbox.value, mailid: openedMailid.value },
          })
        }
      },
    },
    {
      keys: ['?'],
      description: $gettext('Show this help'),
      handler: () => {
        showShortcutHelp.value = true
      },
    },
  ],
  { enabled: computed(() => !mobile.value) }
)

// ----- reading pane width (desktop), persisted -----
const LIST_WIDTH_KEY = 'webmail.listPaneWidth'
const listPaneWidth = ref(
  Number(localStorage.getItem(LIST_WIDTH_KEY)) || 420
)

const paneResizing = ref(false)
const splitRef = ref(null)

const clampPaneWidth = (width) => {
  const max = Math.round(
    (splitRef.value?.clientWidth || window.innerWidth) * 0.6
  )
  return Math.min(Math.max(width, 320), max)
}

// Pointer capture (instead of document mousemove) so the drag keeps working
// when the pointer crosses the reading pane's iframe (which otherwise
// swallows mouse events and freezes the drag), and works with touch/pen.
// The pane edge is measured from the split container instead of assuming a
// fixed 256px sidebar — the sidebar is resizable too.
const startPaneResize = (e) => {
  e.preventDefault()
  const handle = e.currentTarget
  handle.setPointerCapture(e.pointerId)
  paneResizing.value = true
  const splitLeft = splitRef.value.getBoundingClientRect().left
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  let pendingX = e.clientX
  let frame = null
  const onMove = (event) => {
    pendingX = event.clientX
    if (frame) {
      return
    }
    frame = requestAnimationFrame(() => {
      frame = null
      listPaneWidth.value = clampPaneWidth(pendingX - splitLeft)
    })
  }
  const onUp = () => {
    paneResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    if (frame) {
      cancelAnimationFrame(frame)
      frame = null
    }
    localStorage.setItem(LIST_WIDTH_KEY, String(listPaneWidth.value))
    handle.removeEventListener('pointermove', onMove)
    handle.removeEventListener('pointerup', onUp)
    handle.removeEventListener('pointercancel', onUp)
  }
  handle.addEventListener('pointermove', onMove)
  handle.addEventListener('pointerup', onUp)
  handle.addEventListener('pointercancel', onUp)
}

const onDividerKeydown = (e) => {
  if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') {
    return
  }
  e.preventDefault()
  const step = e.key === 'ArrowRight' ? 16 : -16
  listPaneWidth.value = clampPaneWidth(listPaneWidth.value + step)
  localStorage.setItem(LIST_WIDTH_KEY, String(listPaneWidth.value))
}

// ----- open / navigation -----
const onOpenEmail = (mailid) => {
  if (mobile.value) {
    router.push({
      name: 'EmailView',
      query: { mailbox: currentMailbox.value, mailid },
    })
  } else {
    // Query-only change: MailboxView is not remounted, so the list keeps its
    // scroll and accumulated pages. push (not replace) so back/forward walks
    // through the messages the user opened.
    router.push({
      name: 'MailboxView',
      query: { mailbox: currentMailbox.value, mailid },
    })
  }
}

const onPaneDeleted = () => {
  router.replace({
    name: 'MailboxView',
    query: { mailbox: currentMailbox.value },
  })
  webmailStore.listingKey++
}

// A list-side delete removed the message that was open in the pane: just
// clear the pane (the list already updated itself optimistically).
const clearOpenedMail = () => {
  router.replace({
    name: 'MailboxView',
    query: { mailbox: currentMailbox.value },
  })
}

const onPaneLoaded = () => {
  // Backend marks the message seen on content fetch; clear the unseen bar in
  // the list without a refetch.
  if (openedMailid.value) {
    webmailStore.patchEmail(openedMailid.value, { style: '' })
  }
}

// A message deep-linked on desktop should open on the mobile route instead
// (and vice-versa) when crossing the breakpoint or opening a shared URL.
watch(
  [mobile, openedMailid],
  ([isMobile, mailid]) => {
    if (isMobile && mailid) {
      router.replace({ name: 'EmailView', query: route.query })
    }
  },
  { immediate: true }
)

const readOnlyMailbox = computed(() => ['INBOX', 'Sent', 'Drafts', 'Trash', 'Junk'].includes(currentMailbox.value))

// Name of the currently open folder. Prefer the (already translated) label
// from the backend; fall back to the last path segment for nested mailboxes.
const currentFolderLabel = computed(() => {
  const found = userMailboxes.value.find((mb) => mb.name === currentMailbox.value)
  if (found) {
    return found.label.split('/').pop()
  }
  return currentMailbox.value.split(hdelimiter.value || '.').pop()
})

const fetchUserMailboxes = async () => {
  const resp = await api.getUserMailboxes()
  userMailboxes.value = resp.data.mailboxes
  hdelimiter.value = resp.data.hdelimiter
}

const openMailboxForm = () => {
  editedMailbox.value = null
  showMailboxForm.value = true
}

const editMailbox = () => {
  editedMailbox.value = currentMailbox.value
  showMailboxForm.value = true
}

const closeMailboxForm = () => {
  showMailboxForm.value = false
  editedMailbox.value = null
  fetchUserMailboxes()
  // Refresh the drawer's mailbox list too.
  busStore.reloadData()
}

const navigateToMailbox = (mailbox) => {
  router.push({ name: 'MailboxView', query: { mailbox } })
  busStore.reloadData()
}

const compressMailbox = async () => {
  await api.compressUserMailbox({ name: currentMailbox.value })
  busStore.displayNotification({ msg: $gettext('Mailbox compressed') })
}

const deleteMailbox = async () => {
  const confirmed = await confirm.value.open(
    $gettext('Warning'),
    $gettext('Delete this mailbox?'),
    {
      color: 'warning',
      agreeLabel: $gettext('Yes'),
      cancelLabel: $gettext('No'),
    }
  )
  if (!confirmed) {
    return
  }
  await api.deleteUserMailbox({ name: currentMailbox.value })
  busStore.displayNotification({ msg: $gettext('Mailbox deleted') })
  navigateToMailbox('INBOX')
}

watch(() => busStore.dataKey, fetchUserMailboxes)

onMounted(fetchUserMailboxes)
</script>

<style scoped>
/* Fills the height left below the folder header; a horizontal split of
   list + reading pane. min-width/height:0 everywhere so the list and the
   pane's iframe can shrink instead of overflowing (flexbox min-width:auto
   is the classic culprit here). */
.mailbox-split {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
}
.mailbox-split__list {
  flex: 0 0 auto;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
/* 18px gutter with the hairline centered: gives the list and the message
   ~8px of breathing room off the divider on each side, and the whole gutter
   (plus a 2px overhang) is grabbable — ~22px hit zone. The visible line
   stays 1px, thickening to 3px accent on hover/focus/drag. */
.mailbox-split__divider {
  flex: 0 0 18px;
  cursor: col-resize;
  position: relative;
  background: transparent;
  z-index: 1;
  touch-action: none;
  outline: none;
}
.mailbox-split__divider::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: -2px;
  right: -2px;
}
.mailbox-split__divider::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 9px;
  width: 1px;
  background: var(--line-2);
  transition:
    background-color 0.15s ease,
    width 0.15s ease,
    left 0.15s ease;
}
.mailbox-split__divider:hover::after,
.mailbox-split__divider:focus-visible::after,
.mailbox-split__divider.is-dragging::after {
  background: var(--accent);
  width: 3px;
  left: 8px;
}
.mailbox-split__pane {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
