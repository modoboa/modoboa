<template>
  <div class="position-relative h-100">
    <div
      class="compose-view bg-background rounded-lg pa-4 position-relative h-100 d-flex flex-column"
    >
      <v-toolbar>
        <v-btn
          icon="mdi-arrow-left"
          variant="flat"
          :height="btnSize"
          :width="btnSize"
          :aria-label="$gettext('Back')"
          @click="close"
        />
        <div class="d-flex align-center ml-2">
          <v-btn
            v-if="compact"
            icon="mdi-send"
            variant="tonal"
            color="primary"
            :height="btnSize"
            :width="btnSize"
            :loading="working"
            :disabled="loading || converting"
            :title="$gettext('Send')"
            :aria-label="$gettext('Send')"
            @click="submit()"
          />
          <v-btn
            v-else
            prepend-icon="mdi-send"
            variant="tonal"
            color="primary"
            :height="btnSize"
            :loading="working"
            :disabled="loading || converting"
            :text="$gettext('Send')"
            @click="submit()"
          >
          </v-btn>
          <v-btn
            icon
            variant="tonal"
            color="primary"
            :height="btnSize"
            :width="compact ? 36 : 24"
            :aria-label="$gettext('More send options')"
          >
            <v-icon icon="mdi-chevron-down" />
            <v-menu activator="parent">
              <v-list>
                <v-list-item
                  prepend-icon="mdi-send-clock-outline"
                  :title="$gettext('Schedule sending')"
                  @click="openSchedulingForm"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </div>

        <v-spacer />
        <div class="d-flex align-center flex-shrink-0">
          <template v-if="!compact">
            <span v-if="autosaving" class="draft-indicator mr-1" role="status">
              {{ $gettext('Saving…') }}
            </span>
            <span
              v-else-if="draftSavedAt"
              class="draft-indicator mr-1"
              role="status"
            >
              {{ $gettext('Draft saved at %{ time }', { time: draftSavedAt }) }}
            </span>
            <v-btn
              class="ml-1"
              :class="{ 'tb-quiet': !htmlMode }"
              :variant="htmlMode ? 'tonal' : 'text'"
              :color="htmlMode ? 'primary' : undefined"
              icon="mdi-code-tags"
              :height="btnSize"
              :width="btnSize"
              :title="$gettext('HTML mode')"
              :aria-label="$gettext('HTML mode')"
              :aria-pressed="htmlMode ? 'true' : 'false'"
              :loading="converting"
              :disabled="loading"
              @click="toggleHtmlMode"
            />
          </template>
          <v-badge
            class="ml-1"
            :content="attachmentCount"
            :model-value="attachmentCount > 0"
            color="primary"
            offset-x="6"
            offset-y="2"
          >
            <v-btn
              variant="text"
              class="tb-quiet"
              icon="mdi-paperclip"
              :height="btnSize"
              :width="btnSize"
              :title="$gettext('Attachments')"
              :aria-label="$gettext('Attachments')"
              @click="openAttachmentsDialog"
            />
          </v-badge>
          <v-btn
            v-if="!compact"
            class="ml-1 tb-quiet"
            variant="text"
            icon="mdi-content-save-outline"
            :height="btnSize"
            :width="btnSize"
            :title="$gettext('Save as draft')"
            :aria-label="$gettext('Save as draft')"
            :loading="working"
            @click="saveDraft"
          />
          <v-menu :close-on-content-click="false">
            <template #activator="{ props: menuProps }">
              <v-btn
                class="ml-1 tb-quiet"
                variant="text"
                :icon="compact ? 'mdi-dots-vertical' : 'mdi-cog-outline'"
                :height="btnSize"
                :width="btnSize"
                :title="$gettext('Options')"
                :aria-label="$gettext('Options')"
                v-bind="menuProps"
              />
            </template>
            <v-card class="pa-4">
              <!-- Narrow screens: HTML toggle and manual save collapse in here
                   so the toolbar never wraps to a second line. -->
              <template v-if="compact">
                <v-switch
                  :model-value="htmlMode"
                  :disabled="loading || converting"
                  :label="$gettext('HTML mode')"
                  density="compact"
                  hide-details
                  color="primary"
                  @update:model-value="toggleHtmlMode"
                />
                <v-btn
                  block
                  variant="tonal"
                  prepend-icon="mdi-content-save-outline"
                  class="mb-2 mt-1"
                  :text="$gettext('Save as draft')"
                  :loading="working"
                  @click="saveDraft"
                />
              </template>
              <v-switch
                v-model="form.request_dsn"
                :label="$gettext('Request delivery status notification')"
                density="compact"
                hide-details
                color="primary"
              />
              <v-switch
                v-model="form.request_mdn"
                :label="$gettext('Request read receipt')"
                density="compact"
                hide-details
                color="primary"
              />
            </v-card>
          </v-menu>
        </div>
      </v-toolbar>
      <v-form ref="formRef" class="compose-form flex-grow-1 d-flex flex-column">
        <div class="d-flex flex-column gap-3 mb-4">
          <v-select
            v-model="form.sender"
            :label="$gettext('From')"
            :items="allowedSenders"
            item-title="address"
            item-value="address"
            variant="outlined"
            density="compact"
            hide-details="auto"
            :rules="[rules.required]"
            class="mb-3 mt-4"
          />
          <div class="d-flex align-center mb-3">
            <v-combobox
              v-model="form.to"
              :items="contacts"
              :item-title="(item) => getItemTitle(item)"
              return-object
              :label="$gettext('To')"
              :placeholder="$gettext('Provide one or more addresses')"
              persistent-placeholder
              variant="outlined"
              density="compact"
              hide-details="auto"
              chips
              multiple
              :rules="[rules.required]"
              class="flex-grow-1 mr-2"
              @update:search="lookForContacts"
            />
            <v-btn-group density="compact" variant="tonal" class="rounded">
              <v-btn
                v-if="!showCcField"
                :text="$gettext('Cc')"
                :size="mobile ? 'default' : 'small'"
                :min-height="mobile ? 44 : undefined"
                @click="showCcField = true"
              />
              <v-btn
                v-if="!showBccField"
                :text="$gettext('Bcc')"
                :size="mobile ? 'default' : 'small'"
                :min-height="mobile ? 44 : undefined"
                @click="showBccField = true"
              />
            </v-btn-group>
          </div>
          <v-combobox
            v-if="showCcField"
            v-model="form.cc"
            :items="contacts"
            :item-title="(item) => getItemTitle(item)"
            return-object
            :label="$gettext('Cc')"
            :placeholder="$gettext('Provide one or more addresses')"
            persistent-placeholder
            variant="outlined"
            density="compact"
            hide-details="auto"
            chips
            multiple
            :hide-no-data="false"
            class="mb-3"
            append-inner-icon="mdi-close"
            @click:append-inner="showCcField = false"
            @update:search="lookForContacts"
          />
          <v-combobox
            v-if="showBccField"
            v-model="form.bcc"
            :items="contacts"
            :item-title="(item) => getItemTitle(item)"
            return-object
            :label="$gettext('Bcc')"
            :placeholder="$gettext('Provide one or more addresses')"
            persistent-placeholder
            variant="outlined"
            density="compact"
            hide-details="auto"
            chips
            multiple
            :hide-no-data="false"
            class="mb-3"
            append-inner-icon="mdi-close"
            @click:append-inner="showBccField = false"
            @update:search="lookForContacts"
          />
          <v-text-field
            v-model="form.subject"
            :label="$gettext('Subject')"
            variant="outlined"
            density="compact"
            hide-details="auto"
            class="mb-3"
          />
        </div>
        <BodyEditor v-model="form.body" :html-mode="htmlMode" />
        <ConfirmDialog ref="confirmDialog" />
      </v-form>
    </div>
    <v-dialog
      v-model="showAttachmentsDialog"
      :fullscreen="mobile"
      :max-width="mobile ? undefined : 800"
      :transition="mobile ? 'dialog-bottom-transition' : undefined"
    >
      <AttachmentsDialog
        :session-uid="route.query.uid"
        @change="(count) => (attachmentCount = count)"
        @close="closeAttachmentDialog"
      />
    </v-dialog>
    <v-dialog
      v-model="showSchedulingForm"
      :fullscreen="mobile"
      :max-width="mobile ? undefined : 800"
      :transition="mobile ? 'dialog-bottom-transition' : undefined"
    >
      <EmailSchedulingForm @schedule="submit" @close="closeSchedulingForm" />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore, useWebmailStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import debounce from 'debounce'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import AttachmentsDialog from '@/components/webmail/AttachmentsDialog'
import BodyEditor from '@/components/webmail/BodyEditor'
import EmailSchedulingForm from '@/components/webmail/EmailSchedulingForm'
import rules from '@/plugins/rules'
import api from '@/api/webmail'
import contactsApi from '@/api/contacts'

const props = defineProps({
  // Reply to the message given by the route (mailbox, mailid)
  reply: {
    type: Boolean,
    default: false,
  },
  replyAll: {
    type: Boolean,
    default: false,
  },
  // Forward flow: quote the original (subject/body come from the backend's
  // ForwardModifier) but never pre-fill recipients — the user picks them.
  forward: {
    type: Boolean,
    default: false,
  },
})
const route = useRoute()
const router = useRouter()
// `mobile` (< lg by default) keeps driving touch sizing and fullscreen
// dialogs; `compact` (xs, < 600px) drives the toolbar collapse (icon-only
// Send, overflow kebab). Keying the collapse on `mobile` shrank the toolbar
// on any half-width desktop window — way too early.
const { mobile, xs: compact } = useDisplay()
const { isDraftsFolder } = useSpecialFolders(() => route.query.mailbox)
const { $gettext } = useGettext()
const { displayNotification, reloadData } = useBusStore()
const authStore = useAuthStore()
const webmailStore = useWebmailStore()

// 44px touch targets on mobile (WCAG 2.5.8), compact 36px on desktop.
const btnSize = computed(() => (mobile.value ? 44 : 36))

// Only the compose view opened from the drafts folder edits a draft: in
// reply/forward views, route.query.mailid is the original message UID.
const isEditingDraft =
  route.name === 'ComposeEmailView' &&
  isDraftsFolder.value &&
  !!route.query.mailid

const allowedSenders = ref([])
const attachmentCount = ref(0)
const contacts = ref([])
// IMAP uid of the draft backing this composition. The backend's save action
// deletes the previous draft and pushes a new one, returning the NEW uid —
// it must be threaded into every subsequent save or each save duplicates
// the draft.
const draftMailid = ref(
  route.query.draft || (isEditingDraft ? route.query.mailid : null)
)
const draftSavedAt = ref(null)
const autosaving = ref(false)
// Mode actually used in the editor: it decides the format of the message
const htmlMode = ref(false)
const converting = ref(false)
const confirmDialog = ref()
const form = ref({})
const formRef = ref()
const showAttachmentsDialog = ref(false)
const showCcField = ref(false)
const showBccField = ref(false)
const showSchedulingForm = ref(false)
// The form can't be submitted before its content is loaded
const loading = ref(true)
const working = ref(false)

const close = () => {
  router.push({
    name: 'MailboxView',
  })
}

// The conversion is made by the server: the text obtained is the one sent
// as the text part of HTML messages
const convertBody = async (body, source, target) => {
  const resp = await api.convertBody(body, source, target)
  return resp.data.body
}

// An empty editor holds an empty paragraph
const bodyIsEmpty = () =>
  !(form.value.body || '').replace(/<p><\/p>/g, '').trim()

// The plain/HTML switch lives in the toolbar. The content is converted
// (quoted lines become blockquotes and vice versa) instead of reloading the
// original message, which dropped what was written.
const toggleHtmlMode = async () => {
  const source = htmlMode.value ? 'html' : 'plain'
  const target = htmlMode.value ? 'plain' : 'html'
  if (target === 'plain' && !bodyIsEmpty()) {
    // Asked first: the content can't change between the conversion and the
    // answer
    const confirmed = await confirmDialog.value.open(
      $gettext('Switch to plain text'),
      $gettext(
        'The formatting of the message (bold, links, images...) will be lost. Continue?'
      ),
      { agreeLabel: $gettext('Continue') }
    )
    if (!confirmed) {
      return
    }
  }
  converting.value = true
  try {
    form.value.body = await convertBody(form.value.body || '', source, target)
    htmlMode.value = target === 'html'
  } catch {
    // Already displayed to the user by the API client
  } finally {
    converting.value = false
  }
}

// "Name <address>" when the name is known: the API keeps it
const formatRecipient = (rcpt) => {
  if (!rcpt.name) {
    return rcpt.address
  }
  return `"${rcpt.name.replace(/(["\\])/g, '\\$1')}" <${rcpt.address}>`
}

// Is this one of the addresses the user can send from (aliases included)?
const isUserAddress = (address) => {
  const value = address.toLowerCase()
  return (
    value === authStore.authUser.username.toLowerCase() ||
    allowedSenders.value.some((item) => item.address.toLowerCase() === value)
  )
}

// Reply from the address the original message was sent to, when it is one
// of the user's addresses; from the main address otherwise.
const getDefaultSender = (originalEmail) => {
  const recipients = [
    ...(originalEmail?.to || []),
    ...(originalEmail?.cc || []),
  ]
  const sender = allowedSenders.value.find((item) =>
    recipients.some(
      (rcpt) => rcpt.address.toLowerCase() === item.address.toLowerCase()
    )
  )
  if (sender) {
    return sender.address
  }
  return allowedSenders.value[0]?.address || authStore.authUser.username
}

// Leave room to write before the signature, and before or after the
// quoted message
const addSignature = (body, signature, format, above) => {
  const space = format === 'html' ? '<p></p>' : '\n\n'
  if (!body) {
    return space + signature
  }
  if (above) {
    // Paragraphs separate the signature from the quoted message in HTML
    return space + signature + (format === 'html' ? '' : '\n\n') + body
  }
  return body + space + signature
}

// A new message, a reply or a forward
const initForm = async (session, originalEmail) => {
  form.value = {
    sender: getDefaultSender(originalEmail),
    request_dsn: false,
    request_mdn: false,
  }
  // The body of the original message is in the format of the editor
  const format = originalEmail?.body_format || session.editor_format
  let body = ''
  if (originalEmail) {
    let to = []
    if (!props.forward) {
      if (originalEmail.reply_to?.length) {
        // Reply to every Reply-To address
        to = originalEmail.reply_to
      } else if (isUserAddress(originalEmail.from_address.address)) {
        // One's own message: reply to its recipients, not to oneself
        to = originalEmail.to
      } else {
        to = [originalEmail.from_address]
      }
      // "Name <address>" values are kept by the API
      form.value.to = to.map(formatRecipient)
      if (props.replyAll) {
        const excluded = new Set(to.map((rcpt) => rcpt.address.toLowerCase()))
        const cc = []
        for (const rcpt of [...originalEmail.to, ...(originalEmail.cc || [])]) {
          const address = rcpt.address.toLowerCase()
          if (!excluded.has(address) && !isUserAddress(address)) {
            excluded.add(address)
            cc.push(formatRecipient(rcpt))
          }
        }
        form.value.cc = cc
        showCcField.value = cc.length > 0
      }
      if (originalEmail.message_id) {
        form.value.in_reply_to = originalEmail.message_id
        // Keep the whole thread, not only the parent message
        if (originalEmail.references) {
          form.value.references = originalEmail.references
        }
      }
    }
    form.value.subject = originalEmail.subject
    body = originalEmail.body || ''
  }
  if (session.signature) {
    // The signature is in the format of the editor preference
    let signature = session.signature
    if (session.editor_format !== format) {
      signature = await convertBody(signature, session.editor_format, format)
    }
    body = addSignature(
      body,
      signature,
      format,
      session.signature_position !== 'below'
    )
  }
  form.value.body = body
  htmlMode.value = format === 'html'
}

// A draft, in the format it was written in
const initFormFromDraft = (session, draft) => {
  form.value = {
    sender: draft.from_address.address,
    request_dsn: false,
    request_mdn: false,
  }
  if (draft.to?.length) {
    form.value.to = draft.to.map(formatRecipient)
  }
  if (draft.cc?.length) {
    form.value.cc = draft.cc.map(formatRecipient)
    showCcField.value = true
  }
  if (draft.bcc?.length) {
    form.value.bcc = draft.bcc.map(formatRecipient)
    showBccField.value = true
  }
  if (draft.subject) {
    form.value.subject = draft.subject
  }
  form.value.body = draft.body || ''
  // A reply saved as draft stays in its thread
  if (draft.in_reply_to) {
    form.value.in_reply_to = draft.in_reply_to
  }
  if (draft.references) {
    form.value.references = draft.references
  }
  htmlMode.value = (draft.body_format || session.editor_format) === 'html'
}

const prepareMessage = () => {
  const result = { ...form.value }

  for (const field of ['to', 'cc', 'bcc']) {
    if (result[field]?.length) {
      result[field] = result[field].map(getRecipient).filter(Boolean)
    }
  }
  result.body_format = htmlMode.value ? 'html' : 'plain'
  if (draftMailid.value) {
    result.mailid = draftMailid.value
  }
  if ((props.reply || props.forward) && route.query.mailid) {
    // Let the server flag the original message (\Answered, $Forwarded)
    result.original_mailbox = route.query.mailbox
    result.original_mailid = route.query.mailid
    result.original_action = props.forward ? 'forward' : 'reply'
  }
  return result
}

// The sending date is only given to this attempt: if it fails, the next
// click on "Send" must not schedule the message
const submit = async (scheduledDatetime = null) => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const body = prepareMessage()
  if (scheduledDatetime) {
    body.scheduled_datetime = scheduledDatetime
  }
  try {
    await api.sendEmailFromComposeSession(route.query.uid, body)
    // The message went out: drop the backing draft (autosaved or manually
    // saved), otherwise every sent email leaves a stale copy in Drafts.
    if (draftMailid.value) {
      api
        .deleteSelection(webmailStore.specialFolders.draft, [draftMailid.value])
        .catch(() => {})
    }
    router.push({ name: 'MailboxView' })
    reloadData()
    const msg = scheduledDatetime
      ? $gettext('Email scheduled')
      : $gettext('Email sent')
    displayNotification({ msg })
  } catch {
    // Already displayed to the user by the API client
  } finally {
    working.value = false
  }
}

const openAttachmentsDialog = () => {
  showAttachmentsDialog.value = true
}

const closeAttachmentDialog = async () => {
  showAttachmentsDialog.value = false
  const resp = await api.getComposeSession(route.query.uid)
  attachmentCount.value = resp.data.attachments.length
}

const lookForContacts = debounce(async (search) => {
  if (search) {
    const params = { search }
    const resp = await contactsApi.getContacts(params)
    if (resp.data.count > 0) {
      contacts.value = resp.data.results
    }
  } else {
    contacts.value = []
  }
}, 500)

const openSchedulingForm = () => {
  if (!form.value.to?.length) {
    displayNotification({
      msg: $gettext('You must provide one recipient at least'),
      type: 'info',
    })
    return
  }
  showSchedulingForm.value = true
}

const closeSchedulingForm = () => {
  showSchedulingForm.value = false
}

// ----- draft persistence (manual + autosave) -----
// Snapshot of the last state written to the server; used to skip no-op saves
// (including the initial form population / signature insertion).
let lastSavedSnapshot = null
// The save in flight, if any. A second call waits for it instead of
// running alongside it (two concurrent saves would each create a draft
// server-side) or being dropped (a manual "save" during an autosave would
// lose whatever was typed meanwhile).
let saveInFlight = null

const draftSnapshot = () => JSON.stringify(prepareMessage())

const formHasContent = () =>
  Boolean(
    form.value.subject ||
    form.value.body ||
    form.value.to?.length ||
    form.value.cc?.length ||
    form.value.bcc?.length
  )

const persistDraft = async () => {
  if (!route.query.uid) {
    return
  }
  while (saveInFlight) {
    await saveInFlight
  }
  const snapshot = draftSnapshot()
  if (snapshot === lastSavedSnapshot) {
    return
  }
  saveInFlight = writeDraft(snapshot)
  try {
    await saveInFlight
  } finally {
    saveInFlight = null
  }
}

const writeDraft = async (snapshot) => {
  autosaving.value = true
  try {
    const body = prepareMessage()
    const resp = await api.saveComposeSession(route.query.uid, body)
    // Thread the new uid into the next save, or every save duplicates the
    // draft server-side.
    if (resp?.data?.mailid) {
      draftMailid.value = resp.data.mailid
      // Kept in the URL ("draft" parameter) so that reloading the page
      // doesn't lose it and create a duplicate.
      const query = { ...route.query, draft: resp.data.mailid }
      if (isEditingDraft) {
        // The previous version is gone: reloading must open the new one
        query.mailid = resp.data.mailid
      }
      router.replace({ name: route.name, query })
    }
    lastSavedSnapshot = snapshot
    draftSavedAt.value = new Date().toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    // Already displayed to the user by the API client
  } finally {
    autosaving.value = false
  }
}

const saveDraft = async () => {
  working.value = true
  try {
    await persistDraft()
  } finally {
    working.value = false
  }
}

// Autosave: 3s after the last edit. Skips until the initial population
// (draft/reply/signature) has been snapshotted, while sending, and when the
// form has no content yet; persistDraft itself skips no-op saves.
const autosave = debounce(() => {
  if (lastSavedSnapshot === null || working.value || !formHasContent()) {
    return
  }
  persistDraft()
}, 3000)

watch(form, () => autosave(), { deep: true })

onUnmounted(() => {
  // Don't let a pending autosave fire after send/navigation.
  autosave.clear?.()
})

const getContactName = (contact) =>
  contact.display_name ||
  [contact.first_name, contact.last_name].filter(Boolean).join(' ')

const getItemTitle = (item) => {
  if (typeof item === 'string') {
    // Without the quotes of the name: "John Doe" <john@example.com>
    return item.replace(/^"(.*)"(\s*<)/, '$1$2').replace(/\\(["\\])/g, '$1')
  }
  return getContactName(item)
}

// A recipient typed by the user, or a contact picked in the list
const getRecipient = (item) => {
  if (typeof item === 'string') {
    return item
  }
  const address = item.emails?.[0]?.address
  if (!address) {
    return null
  }
  return formatRecipient({ name: getContactName(item), address })
}

const getComposeSession = async () => {
  if (route.query.uid) {
    return (await api.getComposeSession(route.query.uid)).data
  }
  const data = {}
  if (isEditingDraft) {
    data.from_draft_message = route.query.mailid
  } else if (props.forward && route.query.mailbox && route.query.mailid) {
    // The attachments of the forwarded message go along
    data.forward_mailbox = route.query.mailbox
    data.forward_mailid = route.query.mailid
  }
  const session = (await api.createComposeSession(data)).data
  router.replace({
    name: route.name,
    query: { ...route.query, uid: session.uid },
  })
  return session
}

const getEmailContent = async (context) => {
  const resp = await api.getEmailContent(
    route.query.mailbox,
    route.query.mailid,
    { context }
  )
  return resp.data
}

// Everything is loaded before the form is filled: the sender depends on the
// original message and on the allowed addresses, the format on the original
// message (or the draft) and on the preferences. Filling the form as each
// answer arrived lost the signature when the original message came last.
const load = async () => {
  let originalRequest = null
  if ((props.reply || props.forward) && route.query.mailid) {
    originalRequest = getEmailContent(props.forward ? 'forward' : 'reply')
  }
  const draftRequest = isEditingDraft ? getEmailContent('edit') : null
  try {
    const [session, senders, originalEmail, draft] = await Promise.all([
      getComposeSession(),
      api.getAllowedSenders(),
      originalRequest,
      draftRequest,
    ])
    allowedSenders.value = senders.data
    attachmentCount.value = session.attachments?.length || 0
    if (draft) {
      initFormFromDraft(session, draft)
    } else {
      await initForm(session, originalEmail)
    }
    // Baseline for autosave: whatever the form holds after initial population
    // (loaded draft, reply quote, signature) is "already saved" — only real
    // user edits from here on trigger a save.
    lastSavedSnapshot = draftSnapshot()
    loading.value = false
  } catch {
    // Already displayed to the user by the API client
  }
}

load()
</script>

<style scoped>
/* Let the action toolbar wrap to a second line when the buttons don't fit
   (e.g. longer labels in pt-BR like "ENVIAR"/"ANEXOS") instead of forcing a
   horizontal scrollbar. */
.compose-view :deep(.v-toolbar),
.compose-view :deep(.v-toolbar__content) {
  height: auto !important;
}
.compose-view :deep(.v-toolbar__content) {
  flex-wrap: wrap;
  row-gap: 8px;
  padding-block: 8px;
}
/* The user avatar (TopMenu) is position:fixed at the top-right corner with a
   high z-index. On large screens (no mobile app bar above the content) the
   compose toolbar reaches that corner, so reserve room for the avatar —
   page content must never sit under it. */
@media (min-width: 1280px) {
  .compose-view :deep(.v-toolbar__content) {
    padding-right: 68px;
  }
}
/* The webmail shell clips overflow at the viewport (app-shell layout), so
   the form provides its own vertical scroll for long messages; the toolbar
   stays pinned above it. */
.compose-form {
  min-height: 0;
  overflow-y: auto;
}
/* Secondary toolbar actions stay quiet; Send is the single accent. */
.compose-view .tb-quiet {
  color: var(--fg-dim);
}
/* Subtle autosave status next to the toolbar actions. */
.draft-indicator {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--fg-mute);
  white-space: nowrap;
}
</style>
