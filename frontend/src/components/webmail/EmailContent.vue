<template>
  <div class="h-100">
    <div
      v-show="loaded"
      class="email-view bg-background h-100 d-flex flex-column"
    >
      <!-- One accent anchor (Reply); every other action stays quiet, matching
           the list's contextual toolbar language. -->
      <v-toolbar>
        <v-btn
          v-if="showBackButton"
          icon="mdi-arrow-left"
          size="small"
          variant="text"
          class="tb-quiet"
          :title="$gettext('Back')"
          :aria-label="$gettext('Back')"
          @click="emit('close')"
        />

        <div class="d-flex align-center flex-shrink-0">
          <!-- Phones (xs): icon-only Reply so the toolbar stays on one line,
               mirroring the compose Send button. -->
          <v-btn
            v-if="xs"
            icon="mdi-reply"
            height="40"
            width="40"
            variant="tonal"
            color="primary"
            class="reply-btn"
            :title="$gettext('Reply')"
            :aria-label="$gettext('Reply')"
            @click="() => replyToEmail()"
          />
          <v-btn
            v-else
            prepend-icon="mdi-reply"
            height="36"
            variant="tonal"
            color="primary"
            class="reply-btn"
            @click="() => replyToEmail()"
          >
            {{ $gettext('Reply') }}
          </v-btn>
          <v-btn
            :height="xs ? 40 : 36"
            :width="xs ? 36 : 28"
            icon
            variant="tonal"
            color="primary"
            class="reply-btn reply-btn--menu"
            :title="$gettext('More reply options')"
            :aria-label="$gettext('More reply options')"
          >
            <v-icon icon="mdi-chevron-down" />
            <v-menu activator="parent">
              <v-list>
                <v-list-item
                  :title="$gettext('Reply all')"
                  @click="() => replyToEmail(true)"
                />
                <v-list-item
                  :title="$gettext('Forward')"
                  @click="forwardEmail"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </div>
        <v-spacer />
        <!-- Single flex group: the quiet actions wrap to the next row as one
             unit instead of leaving orphans behind. -->
        <div class="d-flex align-center flex-shrink-0">
          <template v-if="mailbox !== 'Scheduled'">
            <v-btn
              v-if="isDraftsFolder"
              class="ml-1 tb-quiet"
              variant="text"
              icon="mdi-pencil"
              size="small"
              :title="$gettext('Edit draft')"
              :aria-label="$gettext('Edit draft')"
              @click="editDraft"
            >
            </v-btn>
            <v-btn
              v-if="isTrashFolder"
              class="ml-1 tb-quiet"
              variant="text"
              icon="mdi-backup-restore"
              size="small"
              :title="$gettext('Restore to Inbox')"
              :aria-label="$gettext('Restore to Inbox')"
              :loading="working"
              @click="restoreEmail"
            >
            </v-btn>
            <v-btn
              v-else-if="isJunkFolder"
              class="ml-1 tb-quiet"
              variant="text"
              icon="mdi-thumb-up"
              size="small"
              :title="$gettext('Mark as not junk')"
              :aria-label="$gettext('Mark as not junk')"
              :loading="working"
              @click="markEmailAsNotJunk"
            >
            </v-btn>
            <v-btn
              v-else
              class="ml-1 tb-quiet"
              variant="text"
              icon="mdi-alert-octagon-outline"
              size="small"
              :title="$gettext('Mark as junk')"
              :aria-label="$gettext('Mark as junk')"
              :loading="working"
              @click="markEmailAsJunk"
            >
            </v-btn>
            <v-btn
              class="ml-1 tb-quiet"
              variant="text"
              icon="mdi-trash-can"
              size="small"
              :title="$gettext('Delete')"
              :aria-label="$gettext('Delete')"
              :loading="working"
              @click="deleteEmail"
            >
            </v-btn>
          </template>
          <v-btn
            class="ml-1 tb-quiet"
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
                  v-if="!enableLinks"
                  :title="$gettext('Enable links')"
                  @click="enableLinks = true"
                />
                <v-list-item
                  v-else
                  :title="$gettext('Disable links')"
                  @click="enableLinks = false"
                />
                <v-list-item
                  v-if="!enableImages"
                  :title="$gettext('Display images')"
                  @click="enableImages = true"
                />
                <v-list-item
                  v-else
                  :title="$gettext('Hide images')"
                  @click="enableImages = false"
                />
                <v-list-item
                  :title="$gettext('Display source')"
                  @click="openEmailSourceDialog"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </div>
      </v-toolbar>

      <nav
        v-if="thread.length > 1"
        class="thread-list"
        :aria-label="$gettext('Messages of the conversation')"
      >
        <div class="thread-list__title">
          {{
            $gettext('%{count} messages in this conversation', {
              count: thread.length,
            })
          }}
        </div>
        <button
          v-for="msg in thread"
          :key="msg.imapid"
          type="button"
          class="thread-list__item"
          :class="{
            'thread-list__item--active':
              String(msg.imapid) === String(currentMailid),
            'thread-list__item--unseen': msg.style === 'unseen',
          }"
          :aria-current="
            String(msg.imapid) === String(currentMailid) ? 'true' : undefined
          "
          @click="openThreadMessage(msg.imapid)"
        >
          <span class="thread-list__from">
            {{ msg.from_address?.name || msg.from_address?.address }}
          </span>
          <v-icon
            v-if="msg.attachments"
            icon="mdi-paperclip"
            size="x-small"
            class="mx-1"
          />
          <span class="thread-list__date">{{ msg.date }}</span>
        </button>
      </nav>
      <div v-if="email" class="email-header">
        <h2>{{ email.subject }}</h2>
        <div class="d-flex">
          <v-menu key="sender">
            <template #activator="{ props: menuProps }">
              <h3 v-bind="menuProps">
                <template v-if="email.from_address.name">
                  {{ email.from_address.name }}
                  <span class="text-grey">
                    &lt;{{ email.from_address.address }}&gt;
                  </span>
                </template>
                <template v-else>
                  {{ email.from_address.address }}
                </template>
              </h3>
            </template>
            <ContactCard v-model="email.from_address" />
          </v-menu>
          <v-spacer />
          <span class="text-grey">{{ email.date }}</span>
        </div>
        <div v-if="email.to?.length" class="text-grey">
          {{ $gettext('To') }}
          <v-menu v-for="(rcpt, index) in email.to" :key="`to-${index}`">
            <template #activator="{ props: menuProps }">
              <span v-if="index > 0">, </span>
              <span v-bind="menuProps">{{ rcpt.name || rcpt.address }}</span>
            </template>
            <ContactCard v-model="email.to[index]" />
          </v-menu>
          <template v-if="email.cc?.length">
            <v-menu v-for="(rcpt, index) in email.cc" :key="`cc-${index}`">
              <template #activator="{ props: menuProps }">
                <span>, </span>
                <span v-bind="menuProps">{{ rcpt.name || rcpt.address }}</span>
              </template>
              <ContactCard v-model="email.cc[index]" />
            </v-menu>
          </template>
        </div>
        <div v-if="email.attachments?.length" class="attachment-list mt-3">
          <v-chip
            v-for="attachment in email.attachments"
            :key="attachment.name"
            size="small"
            label
            prepend-icon="mdi-paperclip"
            class="attachment-chip"
            :title="$gettext('Download attachment')"
            @click="downloadAttachment(attachment.name, attachment.partnum)"
          >
            {{ attachment.name }}
          </v-chip>
        </div>
      </div>
      <v-alert
        v-if="email?.scheduled_datetime"
        type="info"
        variant="tonal"
        density="compact"
        class="mx-1"
      >
        {{ $gettext('Message scheduled at:') }}
        {{ $date(email.scheduled_datetime) }}
      </v-alert>
      <RemoteContentBanner
        v-if="email?.remote_content_blocked && !enableImages"
        class="mx-1 mt-2"
        @show="enableImages = true"
      />
      <div class="email-frame-wrap">
        <!--
          The message body is untrusted: sandboxed iframe (no
          allow-same-origin, so an opaque origin that can't reach the app),
          CSP that only runs our scroll script (see emailFrame.js). :key
          recreates the iframe whenever the document changes (new message,
          links toggled): Chromium does not repaint an in-place srcdoc
          change. See https://issues.chromium.org/issues/555608153
        -->
        <iframe
          v-if="emailDocument"
          :key="emailDocument"
          ref="emailFrame"
          class="email-frame"
          sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
          referrerpolicy="no-referrer"
          :srcdoc="emailDocument"
        />
      </div>
    </div>
    <v-dialog
      v-model="showEmailSource"
      :fullscreen="mobile"
      :max-width="mobile ? undefined : 1200"
      :transition="mobile ? 'dialog-bottom-transition' : undefined"
    >
      <v-card :title="$gettext('Message source')">
        <v-card-text class="text-body-small overflow-x-auto">
          <pre>{{ emailSource }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            :text="$gettext('Close')"
            @click="showEmailSource = false"
          ></v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useProgressStore, useWebmailStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import api from '@/api/webmail'
import ContactCard from '@/components/webmail/ContactCard.vue'
import RemoteContentBanner from '@/components/webmail/RemoteContentBanner.vue'
import { SCROLL_MESSAGE, buildEmailDocument } from './emailFrame'

const props = defineProps({
  mailbox: { type: String, required: true },
  mailid: { type: String, required: true },
  showBackButton: { type: Boolean, default: true },
})

const emit = defineEmits(['close', 'deleted', 'loaded'])

const { $gettext } = useGettext()
const { mobile, xs } = useDisplay()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const progress = useProgressStore()
const router = useRouter()
const { isDraftsFolder, isJunkFolder, isTrashFolder } = useSpecialFolders(
  () => props.mailbox
)

const enableLinks = ref(false)
// Images (embedded and remote) are a separate choice: reading the links
// must not load tracking pixels.
const enableImages = ref(false)
const email = ref(null)
const webmailStore = useWebmailStore()
// In conversation mode, the messages of the conversation are listed above
// the reader and the one clicked is displayed in it.
const currentMailid = ref(props.mailid)
const thread = ref([])
const emailSource = ref(null)
const emailFrame = ref(null)
const loaded = ref(false)
const showEmailSource = ref(false)
const working = ref(false)

const loadThread = async () => {
  thread.value = []
  if (
    webmailStore.listingMode !== 'threaded' ||
    webmailStore.threadingSupported === false
  ) {
    return
  }
  try {
    const resp = await api.getThread(props.mailbox, props.mailid)
    if (resp.data.threading_supported && resp.data.results.length > 1) {
      thread.value = resp.data.results
    }
  } catch {
    // The message itself is still displayed
  }
}

// Display another message of the conversation in the reader
const openThreadMessage = (mailid) => {
  if (String(mailid) === String(currentMailid.value)) {
    return
  }
  currentMailid.value = String(mailid)
  emailSource.value = null
  if (enableLinks.value || enableImages.value) {
    enableLinks.value = false
    enableImages.value = false
  } else {
    fetchMailContent()
  }
}

onMounted(() => {
  fetchMailContent()
  loadThread()
})

watch([enableLinks, enableImages], () => {
  fetchMailContent()
})

// The same instance is reused when the opened message changes (split pane,
// j/k navigation): refetch and drop per-message state. Turning the links or
// the images off already refetches through their watcher, so avoid a double
// fetch.
watch(
  () => props.mailid,
  () => {
    emailSource.value = null
    showEmailSource.value = false
    currentMailid.value = props.mailid
    loadThread()
    if (enableLinks.value || enableImages.value) {
      enableLinks.value = false
      enableImages.value = false
    } else {
      fetchMailContent()
    }
  }
)

const fetchMailContent = () => {
  const options = {
    dformat: 'html',
    links: enableLinks.value ? '1' : '0',
    images: enableImages.value ? '1' : '0',
  }
  api.getEmailContent(props.mailbox, currentMailid.value, options).then((resp) => {
    reloadMailboxCounters()
    // New key with the new body: one fresh iframe per message.
    email.value = resp.data
    const item = thread.value.find(
      (msg) => String(msg.imapid) === String(currentMailid.value)
    )
    if (item) {
      // Opening a message marks it as read
      item.style = ''
    }
    nextTick(() => {
      // Reading progress for the global top bar: the sandboxed document
      // reports its scroll through postMessage (onFrameMessage).
      progress.setScroll(0)
      loaded.value = true
      emit('loaded', email.value)
    })
  })
}

// Styles injected in every message document. Exactly one scroll container
// (the iframe viewport), sane typography for unstyled mail, no overflow on
// phones, and the app's scrollbar (the iframe is a separate document).
const FRAME_STYLE = `
          /* Exactly ONE scroll container: the iframe viewport (html).
             Setting any overflow on <body> turns it into a second scroll
             container (overflow-x:hidden computes overflow-y:auto), and
             marketing emails ship body{height:100%} — result: two
             scrollbars side by side and a body that scrolls where the
             window's scroll listener (reading progress) can't see it. */
          html {
            height: auto !important;
            max-width: 100% !important;
            /* auto, not hidden: anything that still can't shrink (fixed-width
               tables etc.) becomes scrollable instead of cut off. */
            overflow-x: auto !important;
            overflow-y: auto !important;
            word-wrap: break-word !important;
            box-sizing: border-box !important;
          }
          body {
            height: auto !important;
            min-height: 0 !important;
            max-width: 100% !important;
            overflow: visible !important;
            word-wrap: break-word !important;
            box-sizing: border-box !important;
          }
          /* Base typography for messages that bring no styling of their own
             (plain transactional mail would otherwise render in browser
             default serif, glued to the frame edges). Deliberately body-level
             only: styled emails keep their own look. */
          body {
            margin: 0;
            padding: 18px 22px;
            font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial,
              sans-serif;
            font-size: 15px;
            line-height: 1.55;
            color: #1c1c1c;
          }
          img, table, video, canvas, svg {
            max-width: 100% !important;
            height: auto !important;
          }
          /* Plain-text mail arrives as <pre> (backend viewmail_plain), and
             pre never wraps: long lines (cron logs, URLs) were clipped at
             the frame edge on phones. Wrap instead. */
          pre {
            white-space: pre-wrap !important;
            word-break: break-word !important;
          }
          /* Same scrollbar as the rest of the app (portfolio.scss) — the
             iframe is a separate document, so the site-wide rules don't
             reach it. Hex values inlined from the --accent/--accent-2
             tokens, which don't exist in here either. */
          * {
            scrollbar-width: thin;
            scrollbar-color: #7c5cff #050505;
          }
          ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
          }
          ::-webkit-scrollbar-track {
            background: #050505;
          }
          ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #7c5cff, #4a32cf);
            border: 2px solid #050505;
          }
          ::-webkit-scrollbar-thumb:hover {
            background: #a594ff;
          }
`

const emailDocument = computed(() =>
  buildEmailDocument(email.value?.body, {
    enableImages: enableImages.value,
    style: FRAME_STYLE,
  })
)

const onFrameMessage = (event) => {
  // Only trust our own frame: any other window can post messages too.
  if (
    !emailFrame.value ||
    event.source !== emailFrame.value.contentWindow ||
    event.data?.type !== SCROLL_MESSAGE
  ) {
    return
  }
  const value = Number(event.data.value)
  progress.setScroll(
    Number.isFinite(value) ? Math.min(Math.max(value, 0), 1) : 0
  )
}

onMounted(() => window.addEventListener('message', onFrameMessage))
onUnmounted(() => window.removeEventListener('message', onFrameMessage))

const downloadAttachment = (name, part) => {
  api.getEmailAttachment(props.mailbox, currentMailid.value, part).then((resp) => {
    const blob = new Blob([resp.data], { type: resp.headers['Content-Type'] })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = name
    link.click()
    URL.revokeObjectURL(link.href)
  })
}

const deleteEmail = () => {
  working.value = true
  api
    .deleteSelection(props.mailbox, [currentMailid.value])
    .then(() => {
      displayNotification({ msg: $gettext('Message deleted') })
      reloadMailboxCounters()
      emit('deleted')
    })
    .finally(() => {
      working.value = false
    })
}

const restoreEmail = () => {
  working.value = true
  api
    .moveSelection(props.mailbox, 'INBOX', [currentMailid.value])
    .then(() => {
      displayNotification({ msg: $gettext('Message restored to Inbox') })
      reloadMailboxCounters()
      emit('deleted')
    })
    .finally(() => {
      working.value = false
    })
}

const markEmailAsJunk = () => {
  working.value = true
  api
    .markSelectionAsJunk(props.mailbox, [currentMailid.value])
    .then(() => {
      displayNotification({ msg: $gettext('Message marked as junk') })
      reloadMailboxCounters()
      emit('deleted')
    })
    .finally(() => {
      working.value = false
    })
}

const markEmailAsNotJunk = () => {
  working.value = true
  api
    .markSelectionAsNotJunk(props.mailbox, [currentMailid.value])
    .then(() => {
      displayNotification({ msg: $gettext('Message marked as not junk') })
      reloadMailboxCounters()
      emit('deleted')
    })
    .finally(() => {
      working.value = false
    })
}

const openEmailSourceDialog = async () => {
  if (!emailSource.value) {
    const resp = await api.getEmailSource(props.mailbox, currentMailid.value)
    emailSource.value = resp.data.source
  }
  showEmailSource.value = true
}

const replyToEmail = (all) => {
  const query = { mailbox: props.mailbox, mailid: currentMailid.value }
  if (all) {
    query.all = all
  }
  router.push({ name: 'ReplyEmailView', query })
}

const forwardEmail = () => {
  router.push({
    name: 'ForwardEmailView',
    query: { mailbox: props.mailbox, mailid: currentMailid.value },
  })
}

const editDraft = () => {
  router.push({
    name: 'ComposeEmailView',
    query: { mailbox: props.mailbox, mailid: currentMailid.value },
  })
}
</script>

<style>
/* The view is a flex column: toolbar + header + (optional alert) in flow,
   then the message frame fills whatever height is left. No JS positioning,
   so the body never slides up from the bottom or fails to anchor. */
.email-view {
  height: 100%;
  min-height: 0;
}
/* Let the action toolbar wrap to a second line when the buttons don't fit
   (e.g. longer labels in pt-BR like "RESPONDER") instead of forcing a
   horizontal scrollbar. */
.email-view .v-toolbar,
.email-view .v-toolbar__content {
  height: auto !important;
}
.email-view .v-toolbar__content {
  flex-wrap: wrap;
  row-gap: 8px;
  padding-block: 8px;
}
/* Reading-view actions reach the 44px touch minimum on small screens. */
@media (max-width: 960px) {
  .email-view .v-toolbar__content .v-btn {
    min-width: 44px;
    min-height: 44px;
  }
}
/* Quiet toolbar actions (accent lives on the Reply anchor only). */
.email-view .tb-quiet {
  color: var(--fg-dim);
}
/* The wrapper owns the flex sizing so the iframe can be swapped freely
   inside it without touching the column layout. A hairline frames the light
   canvas so it reads as a document inside the dark UI instead of a bare
   white wall touching the pane edges. */
.email-frame-wrap {
  flex: 1 1 auto;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  margin-top: 12px;
  border: 1px solid var(--line-2);
  background-color: #fff;
}
.email-frame {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  overflow-y: auto;
  border: none;
  /* The rendered email keeps a light canvas (messages assume white). */
  background-color: #fff;
  /* Soft fade-in instead of an abrupt white pop. */
  animation: email-frame-in 0.3s ease both;
}
/* Attachment chips under the recipients. */
.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.attachment-chip {
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 11px !important;
  letter-spacing: 0.02em;
}

@keyframes email-frame-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Message header is app chrome, not email content. Flush with the content
   edge (no side padding) so the subject lines up with the body below; a
   single bottom rule separates it from the rendered email. */
/* Messages of the conversation: a compact list above the reader, capped so
   the message body keeps most of the height. */
.thread-list {
  flex: 0 0 auto;
  max-height: 30%;
  overflow-y: auto;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--line-2);
}
.thread-list__title {
  padding: 4px 0;
  font-size: 12px;
  color: var(--fg-dim);
}
.thread-list__item {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 36px;
  padding: 4px 8px;
  border-left: 3px solid transparent;
  border-radius: 4px;
  text-align: left;
  color: inherit;
  background: none;
  cursor: pointer;
}
.thread-list__item:hover,
.thread-list__item:focus-visible {
  background: rgba(124, 92, 255, 0.08);
}
.thread-list__item--active {
  border-left-color: var(--accent, #7c5cff);
  background: rgba(124, 92, 255, 0.12);
}
.thread-list__item--unseen .thread-list__from {
  font-weight: 700;
}
.thread-list__from {
  flex: 1 1 auto;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.thread-list__date {
  flex: 0 0 auto;
  margin-left: 8px;
  font-size: 12px;
  color: var(--fg-dim);
  font-variant-numeric: tabular-nums;
}
.email-header {
  padding: 4px 0 16px;
  border-bottom: 1px solid var(--line-2);
}
.email-header > .d-flex {
  flex-wrap: wrap;
  row-gap: 4px;
  align-items: center;
}
.email-header > .d-flex > .text-grey {
  flex-shrink: 0;
  margin-left: 12px;
}
.email-header h2 {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(16px, 5vw, 24px);
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: var(--fg);
  word-break: break-word;
  overflow-wrap: break-word;
}
.email-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(11px, 2.8vw, 13px) !important;
  letter-spacing: -0.01em;
  color: var(--fg);
  word-break: break-word;
  overflow-wrap: break-word;
}
.email-header h3 span,
.email-header .text-grey,
.email-header .text-grey span,
.email-header a {
  font-family: var(--font-mono) !important;
  font-size: clamp(9px, 2.5vw, 11px) !important;
  letter-spacing: 0.03em !important;
  word-break: break-word;
  overflow-wrap: break-word;
}
.email-header > .d-flex > .text-grey {
  white-space: nowrap !important;
}
</style>
