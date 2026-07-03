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
            v-if="mailbox === constants.DRAFTS_FOLDER"
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
            v-if="mailbox === 'Trash'"
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
            v-else-if="mailbox === 'Junk'"
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
                :title="$gettext('Display source')"
                @click="openEmailSourceDialog"
              />
            </v-list>
          </v-menu>
        </v-btn>
        </div>
      </v-toolbar>

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
      <div ref="frameWrapper" class="email-frame-wrap">
        <iframe class="email-frame" />
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
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useProgressStore } from '@/stores'
import constants from '@/constants.json'
import api from '@/api/webmail'
import ContactCard from '@/components/webmail/ContactCard.vue'

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

const enableLinks = ref(false)
const email = ref(null)
const emailSource = ref(null)
const frameWrapper = ref(null)
const loaded = ref(false)
const showEmailSource = ref(false)
const working = ref(false)

onMounted(() => {
  fetchMailContent()
})

watch(enableLinks, () => {
  fetchMailContent()
})

// The same instance is reused when the opened message changes (split pane,
// j/k navigation): refetch and drop per-message state. Turning enableLinks
// off already refetches through its own watcher, so avoid a double fetch.
watch(
  () => props.mailid,
  () => {
    emailSource.value = null
    showEmailSource.value = false
    if (enableLinks.value) {
      enableLinks.value = false
    } else {
      fetchMailContent()
    }
  }
)

const fetchMailContent = () => {
  const options = {
    dformat: 'html',
    links: enableLinks.value ? '1' : '0',
  }
  api.getEmailContent(props.mailbox, props.mailid, options).then((resp) => {
    reloadMailboxCounters()
    email.value = resp.data
    nextTick(() => {
      if (!frameWrapper.value) {
        return
      }
      // Rebuild the iframe on every fetch: writing into a fresh document is
      // the only reliable way to reset scripts/styles from the previous
      // message. Scoped to this component's wrapper (never a global query).
      const iframe = document.createElement('iframe')
      iframe.classList.add('email-frame')
      frameWrapper.value.replaceChildren(iframe)
      if (email.value.body) {
        const iframeDoc = iframe.contentDocument
        iframeDoc.write(email.value.body)
        // Add style to prevent content overflow inside iframe on small screens
        const style = iframeDoc.createElement('style')
        style.textContent = `
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
        iframeDoc.head.appendChild(style)
        iframeDoc.close()
      }
      // Feed the global top bar with reading progress. The body lives in a
      // separate iframe document, so its scroll never reaches the parent's
      // capture-phase listener — bind it here (re-bound on every fetch since
      // the iframe element is replaced above).
      progress.setScroll(0)
      bindIframeScroll(iframe)
      loaded.value = true
      emit('loaded', email.value)
    })
  })
}

const bindIframeScroll = (iframe) => {
  const win = iframe.contentWindow
  if (!win) {
    return
  }
  win.addEventListener(
    'scroll',
    () => {
      const doc =
        iframe.contentDocument?.scrollingElement ||
        iframe.contentDocument?.documentElement
      if (!doc) {
        return
      }
      const max = doc.scrollHeight - doc.clientHeight
      progress.setScroll(max > 0 ? doc.scrollTop / max : 0)
    },
    { passive: true }
  )
}

const downloadAttachment = (name, part) => {
  api.getEmailAttachment(props.mailbox, props.mailid, part).then((resp) => {
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
  api.deleteSelection(props.mailbox, [props.mailid]).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message deleted') })
    reloadMailboxCounters()
    emit('deleted')
  })
}

const restoreEmail = () => {
  working.value = true
  api.moveSelection(props.mailbox, 'INBOX', [props.mailid]).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message restored to Inbox') })
    reloadMailboxCounters()
    emit('deleted')
  })
}

const markEmailAsJunk = () => {
  working.value = true
  api.markSelectionAsJunk(props.mailbox, [props.mailid]).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message marked as junk') })
    reloadMailboxCounters()
    emit('deleted')
  })
}

const markEmailAsNotJunk = () => {
  working.value = true
  api.markSelectionAsNotJunk(props.mailbox, [props.mailid]).then(() => {
    working.value = false
    displayNotification({ msg: $gettext('Message marked as not junk') })
    reloadMailboxCounters()
    emit('deleted')
  })
}

const openEmailSourceDialog = async () => {
  if (!emailSource.value) {
    const resp = await api.getEmailSource(props.mailbox, props.mailid)
    emailSource.value = resp.data.source
  }
  showEmailSource.value = true
}

const replyToEmail = (all) => {
  const query = { mailbox: props.mailbox, mailid: props.mailid }
  if (all) {
    query.all = all
  }
  router.push({ name: 'ReplyEmailView', query })
}

const forwardEmail = () => {
  router.push({
    name: 'ForwardEmailView',
    query: { mailbox: props.mailbox, mailid: props.mailid },
  })
}

const editDraft = () => {
  router.push({
    name: 'ComposeEmailView',
    query: { mailid: props.mailid },
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
