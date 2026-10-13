<template>
  <div
    class="position-relative h-100"
    @dragenter="onDragEnter"
    @paste.capture="onPaste"
  >
    <div
      class="bg-white rounded-lg pa-4 position-relative h-100 d-flex flex-column"
    >
      <v-toolbar color="white">
        <v-btn
          icon="mdi-arrow-left"
          size="small"
          variant="flat"
          @click="close"
        />
        <v-btn-group color="primary" rounded="lg" density="compact" divided>
          <v-btn
            class="ml-2"
            prepend-icon="mdi-send"
            :disabled="loading || uploading"
            :loading="working"
            :text="$gettext('Send')"
            @click="submit()"
          >
          </v-btn>
          <v-btn size="small" icon :disabled="loading || uploading">
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
        </v-btn-group>

        <v-menu :close-on-content-click="false">
          <template #activator="{ props: menuProps }">
            <v-btn
              class="ml-2"
              variant="tonal"
              prepend-icon="mdi-cog-outline"
              :text="$gettext('Options')"
              v-bind="menuProps"
            />
          </template>
          <v-card class="pa-4">
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
        <v-btn
          class="ml-2"
          variant="tonal"
          prepend-icon="mdi-paperclip"
          :disabled="loading"
          :text="$gettext('Attach')"
          @click="fileInput.click()"
        />
        <input
          ref="fileInput"
          type="file"
          multiple
          hidden
          @change="onFilesSelected"
        />
        <v-btn
          class="ml-2"
          icon="mdi-content-save-outline"
          size="small"
          :title="$gettext('Save as draft')"
          :disabled="loading || uploading"
          :loading="working"
          @click="saveDraft"
        />
      </v-toolbar>
      <v-form ref="formRef" class="flex-grow-1 d-flex flex-column">
        <div>
          <v-row class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('From') }}</span>
            </v-col>
            <v-col cols="8">
              <v-select
                v-model="form.sender"
                :items="allowedSenders"
                item-title="address"
                item-value="address"
                variant="outlined"
                density="compact"
                hide-details="auto"
                :rules="[rules.required]"
              />
            </v-col>
          </v-row>
          <v-row class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('To') }}</span>
            </v-col>
            <v-col cols="8">
              <v-combobox
                v-model="form.to"
                :items="contacts"
                :item-title="(item) => getItemTitle(item)"
                return-object
                :placeholder="$gettext('Provide one or more addresses')"
                variant="outlined"
                density="compact"
                hide-details="auto"
                chips
                multiple
                :rules="[rules.required]"
                @update:search="lookForContacts"
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                v-if="!showCcField"
                :text="$gettext('Cc')"
                prepend-icon="mdi-plus"
                size="x-small"
                variant="flat"
                @click="showCcField = true"
              />
              <v-btn
                v-if="!showBccField"
                :text="$gettext('Bcc')"
                prepend-icon="mdi-plus"
                size="x-small"
                variant="flat"
                @click="showBccField = true"
              />
            </v-col>
          </v-row>
          <v-row v-if="showCcField" class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('Cc') }}</span>
              <v-btn
                icon="mdi-close"
                variant="flat"
                size="x-small"
                @click="showCcField = false"
              />
            </v-col>
            <v-col cols="8">
              <v-combobox
                v-model="form.cc"
                :items="contacts"
                :item-title="(item) => getItemTitle(item)"
                return-object
                :placeholder="$gettext('Provide one or more addresses')"
                variant="outlined"
                density="compact"
                hide-details="auto"
                chips
                multiple
                :hide-no-data="false"
                @update:search="lookForContacts"
              />
            </v-col>
          </v-row>
          <v-row v-if="showBccField" class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('Bcc') }}</span>
              <v-btn
                icon="mdi-close"
                variant="flat"
                size="x-small"
                @click="showBccField = false"
              />
            </v-col>
            <v-col cols="8">
              <v-combobox
                v-model="form.bcc"
                :items="contacts"
                :item-title="(item) => getItemTitle(item)"
                return-object
                :placeholder="$gettext('Provide one or more addresses')"
                variant="outlined"
                density="compact"
                hide-details="auto"
                chips
                multiple
                :hide-no-data="false"
                @update:search="lookForContacts"
              />
            </v-col>
          </v-row>
          <v-row class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('Subject') }}</span>
            </v-col>
            <v-col cols="8">
              <v-text-field
                v-model="form.subject"
                variant="outlined"
                density="compact"
                hide-details="auto"
              />
            </v-col>
          </v-row>
          <v-row v-if="attachments.length" class="align-center">
            <v-col cols="2">
              <span>{{ $gettext('Attachments') }}</span>
            </v-col>
            <v-col cols="8">
              <v-chip
                v-for="attachment in attachments"
                :key="attachment.tmpname || attachment.fname"
                class="ma-1"
                :closable="!isUploading(attachment)"
                :close-label="$gettext('Remove')"
                @click:close="removeAttachment(attachment)"
              >
                <template #prepend>
                  <v-progress-circular
                    v-if="isUploading(attachment)"
                    class="mr-2"
                    :model-value="attachment.progress"
                    size="16"
                    width="2"
                  />
                  <v-icon v-else icon="mdi-paperclip" start />
                </template>
                {{ attachment.fname }}
                <span v-if="attachment.size" class="ml-1 text-medium-emphasis">
                  ({{ $filesize(attachment.size) }})
                </span>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <BodyEditor
          ref="bodyEditor"
          v-model="form.body"
          v-model:format="bodyFormat"
        />
      </v-form>
    </div>
    <div
      v-if="dragging"
      class="drop-overlay d-flex ga-4 pa-4"
      @dragover.prevent
      @dragleave="onDragLeave"
      @drop.prevent="dragging = false"
    >
      <div
        class="drop-zone rounded-lg d-flex align-center justify-center text-h6"
        :class="{ 'drop-zone-active': dropInline === false }"
        @dragenter="dropInline = false"
        @drop.prevent.stop="onDrop($event, false)"
      >
        <v-icon icon="mdi-paperclip" class="mr-2" />
        {{ $gettext('Drop files to attach them') }}
      </div>
      <div
        v-if="bodyFormat === 'html'"
        class="drop-zone rounded-lg d-flex align-center justify-center text-h6"
        :class="{ 'drop-zone-active': dropInline === true }"
        @dragenter="dropInline = true"
        @drop.prevent.stop="onDrop($event, true)"
      >
        <v-icon icon="mdi-image-outline" class="mr-2" />
        {{ $gettext('Drop images to insert them in the message') }}
      </div>
    </div>
    <v-dialog v-model="showSchedulingForm" max-width="800">
      <EmailSchedulingForm @schedule="submit" @close="closeSchedulingForm" />
    </v-dialog>
    <ConfirmDialog ref="confirmDialog" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import debounce from 'debounce'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import BodyEditor from '@/components/webmail/BodyEditor'
import EmailSchedulingForm from '@/components/webmail/EmailSchedulingForm'
import rules from '@/plugins/rules'
import api from '@/api/webmail'
import contactsApi from '@/api/contacts'

// In reply and forward modes, route.query.mailbox and route.query.mailid
// designate the original message
const props = defineProps({
  reply: {
    type: Boolean,
    default: false,
  },
  replyAll: {
    type: Boolean,
    default: false,
  },
  // Forwarding: recipients must be chosen by the user
  forward: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { isDraftsFolder } = useSpecialFolders(() => route.query.mailbox)
const { $gettext, $pgettext } = useGettext()
const { displayNotification, reloadData } = useBusStore()
const authStore = useAuthStore()

// Only the compose view opened from the drafts folder edits a draft: in
// reply/forward views, route.query.mailid is the original message UID.
const isEditingDraft =
  route.name === 'ComposeEmailView' &&
  isDraftsFolder.value &&
  !!route.query.mailid

const allowedSenders = ref([])
// UID of the draft being edited, updated on each save so the previous
// version gets replaced instead of duplicated. It is kept in the URL
// ("draft" parameter) so that reloading the page doesn't lose it.
const draftMailid = ref(
  route.query.draft || (isEditingDraft ? route.query.mailid : null)
)
// Uploaded attachments, and the ones being uploaded (with a progress)
const attachments = ref([])
// Format of the message, decided once everything is loaded, then changed by
// the user only
const bodyFormat = ref('plain')
const contacts = ref([])
const form = ref({})
const confirmDialog = ref()
const bodyEditor = ref()
const dragging = ref(false)
// Zone of the overlay under the pointer: insert images in the message, or
// attach the files
const dropInline = ref(null)
const fileInput = ref()
const formRef = ref()
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
      form.value.to = to.map(formatRecipient)
    }
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
    form.value.subject = originalEmail.subject
    body = originalEmail.body || ''
    if (originalEmail.message_id) {
      form.value.in_reply_to = originalEmail.message_id
      // Keep the whole thread, not only the parent message
      if (originalEmail.references) {
        form.value.references = originalEmail.references
      }
    }
  }
  if (session.signature) {
    // The signature is in the format of the editor preference
    let signature = session.signature
    if (session.editor_format !== format) {
      const resp = await api.convertBody(
        signature,
        session.editor_format,
        format
      )
      signature = resp.data.body
    }
    body = addSignature(
      body,
      signature,
      format,
      session.signature_position !== 'below'
    )
  }
  form.value.body = body
  bodyFormat.value = format
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
  bodyFormat.value = draft.body_format || session.editor_format
}

const prepareMessage = () => {
  const result = { ...form.value }

  for (const field of ['to', 'cc', 'bcc']) {
    if (result[field]?.length) {
      result[field] = result[field].map(getRecipient).filter(Boolean)
    }
  }
  result.body_format = bodyFormat.value
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
  if (!valid || !(await confirmSending())) {
    return
  }
  working.value = true
  const body = prepareMessage()
  if (scheduledDatetime) {
    body.scheduled_datetime = scheduledDatetime
  }
  try {
    await api.sendEmailFromComposeSession(route.query.uid, body)
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

// Words announcing an attachment, in English and in the user's language:
// a word starting with one of them is enough
const ATTACHMENT_WORDS = ['attach', 'enclos']

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// Does the text written by the user (quoted messages excluded) mention an
// attachment?
const mentionsAttachment = () => {
  let text = form.value.body || ''
  if (bodyFormat.value === 'html') {
    const doc = new DOMParser().parseFromString(text, 'text/html')
    doc.querySelectorAll('blockquote').forEach((node) => node.remove())
    text = doc.body.textContent
  } else {
    text = text
      .split('\n')
      .filter((line) => !line.startsWith('>'))
      .join('\n')
  }
  const words = [
    ...ATTACHMENT_WORDS,
    ...$pgettext(
      'Beginnings of words announcing an attachment, separated by commas',
      'attach,enclos'
    ).split(','),
  ]
    .map((word) => escapeRegExp(word.trim()))
    .filter(Boolean)
  return new RegExp(`(^|[^\\p{L}])(${words.join('|')})`, 'iu').test(text)
}

const confirmSending = async () => {
  const options = { agreeLabel: $gettext('Send anyway') }
  if (
    !form.value.subject?.trim() &&
    !(await confirmDialog.value.open(
      $gettext('Empty subject'),
      $gettext('This message has no subject.'),
      options
    ))
  ) {
    return false
  }
  if (
    !attachments.value.length &&
    mentionsAttachment() &&
    !(await confirmDialog.value.open(
      $gettext('Forgotten attachment?'),
      $gettext('The message mentions an attachment, but none is attached.'),
      options
    ))
  ) {
    return false
  }
  return true
}

const isUploading = (attachment) => attachment.progress !== undefined

// Send and save wait for the uploads to complete
const uploading = computed(() => attachments.value.some(isUploading))

// One file at a time: the server rewrites the whole session for each one,
// concurrent uploads would lose attachments
const uploadFiles = async (files) => {
  if (loading.value) {
    return
  }
  for (const file of files) {
    attachments.value.push({ fname: file.name, size: file.size, progress: 0 })
    const attachment = attachments.value[attachments.value.length - 1]
    const formData = new FormData()
    formData.append('attachment', file)
    try {
      const resp = await api.uploadAttachment(
        route.query.uid,
        formData,
        (event) => {
          attachment.progress = event.total
            ? (100 * event.loaded) / event.total
            : 0
        }
      )
      delete attachment.progress
      Object.assign(attachment, resp.data)
    } catch {
      // Already displayed to the user by the API client
      attachments.value.splice(attachments.value.indexOf(attachment), 1)
    }
  }
}

const removeAttachment = async (attachment) => {
  try {
    await api.removeAttachment(route.query.uid, attachment.tmpname)
  } catch {
    // Already displayed to the user by the API client
    return
  }
  attachments.value.splice(attachments.value.indexOf(attachment), 1)
}

const onFilesSelected = (event) => {
  // Copied: the list is emptied with the input, to select the same file again
  const files = [...event.target.files]
  event.target.value = ''
  uploadFiles(files)
}

// Images most mail clients display within a message
const isInlineImage = (file) => /^image\/(png|jpeg|gif|webp)$/.test(file.type)

// Images go in the body of HTML messages when asked, other files are
// attached
const addFiles = (files, inline) => {
  const images = inline ? files.filter(isInlineImage) : []
  if (images.length) {
    bodyEditor.value.insertImages(images)
  }
  uploadFiles(files.filter((file) => !images.includes(file)))
}

// Only files are dropped here: text dragged inside the editor is not
const onDragEnter = (event) => {
  if (!loading.value && event.dataTransfer?.types.includes('Files')) {
    dragging.value = true
  }
}

// Fired when the pointer moves from a zone to another one too
const onDragLeave = (event) => {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragging.value = false
    dropInline.value = null
  }
}

const onDrop = (event, inline) => {
  dragging.value = false
  dropInline.value = null
  addFiles([...event.dataTransfer.files], inline)
}

// Captured before the editor gets them: pasted files are attached, except
// images pasted in the editor of an HTML message
const onPaste = (event) => {
  const files = [...(event.clipboardData?.files || [])]
  if (files.length) {
    event.preventDefault()
    event.stopPropagation()
    const inline =
      bodyFormat.value === 'html' && !!event.target.closest?.('.ProseMirror')
    addFiles(files, inline)
  }
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

const saveDraft = async () => {
  working.value = true
  const body = prepareMessage()
  try {
    const resp = await api.saveComposeSession(route.query.uid, body)
    draftMailid.value = resp.data.mailid
    const query = { ...route.query, draft: resp.data.mailid }
    if (isEditingDraft) {
      // The previous version is gone: reloading must open the new one
      query.mailid = resp.data.mailid
    }
    router.replace({ name: route.name, query })
    displayNotification({ msg: $gettext('Draft saved') })
  } catch {
    // Already displayed to the user by the API client
  } finally {
    working.value = false
  }
}

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
// message (or the draft) and on the preferences.
const load = async () => {
  let originalRequest = null
  if (props.reply || props.forward) {
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
    attachments.value = session.attachments || []
    if (draft) {
      initFormFromDraft(session, draft)
    } else {
      await initForm(session, originalEmail)
    }
    loading.value = false
  } catch {
    // Already displayed to the user by the API client
  }
}

load()
</script>

<style scoped>
.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: rgba(var(--v-theme-surface), 0.9);
}

.drop-zone {
  flex: 1;
  border: 2px dashed rgb(var(--v-theme-primary));
}

.drop-zone-active {
  background: rgba(var(--v-theme-primary), 0.12);
}

/* The drop events target the zone, not its icon or text */
.drop-zone > * {
  pointer-events: none;
}
</style>
