<template>
  <div class="position-relative h-100">
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
            :disabled="loading"
            :loading="working"
            :text="$gettext('Send')"
            @click="submit()"
          >
          </v-btn>
          <v-btn size="small" icon :disabled="loading">
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
          :text="$gettext('Attachments') + ` (${attachmentCount})`"
          @click="openAttachmentsDialog"
        />
        <v-btn
          class="ml-2"
          icon="mdi-content-save-outline"
          size="small"
          :title="$gettext('Save as draft')"
          :disabled="loading"
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
                item-title="display_name"
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
                item-title="display_name"
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
        </div>
        <BodyEditor v-model="form.body" v-model:format="bodyFormat" />
      </v-form>
    </div>
    <v-dialog v-model="showAttachmentsDialog" max-width="800">
      <AttachmentsDialog
        :session-uid="route.query.uid"
        @close="closeAttachmentDialog"
      />
    </v-dialog>
    <v-dialog v-model="showSchedulingForm" max-width="800">
      <EmailSchedulingForm @schedule="submit" @close="closeSchedulingForm" />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import debounce from 'debounce'
import AttachmentsDialog from '@/components/webmail/AttachmentsDialog'
import BodyEditor from '@/components/webmail/BodyEditor'
import { convertBody } from '@/utils/bodyFormat'
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
const { $gettext } = useGettext()
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
const attachmentCount = ref(0)
// Format of the message, decided once everything is loaded, then changed by
// the user only
const bodyFormat = ref('plain')
const contacts = ref([])
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

// A new message, a reply or a forward
const initForm = (session, originalEmail) => {
  form.value = {
    sender: getDefaultSender(originalEmail),
    request_dsn: false,
    request_mdn: false,
  }
  // The body of the original message is in the format of the editor
  const format = originalEmail?.body_format || session.editor_format
  let body = ''
  if (originalEmail) {
    if (!props.forward) {
      // Reply to every Reply-To address if any, to the sender otherwise
      form.value.to = originalEmail.reply_to?.length
        ? originalEmail.reply_to.map((rcpt) => rcpt.address)
        : [originalEmail.from_address.address]
    }
    if (props.replyAll) {
      // Bare addresses only: the API rejects "Name <address>" values
      const excluded = new Set(form.value.to || [])
      const addresses = [...originalEmail.to, ...(originalEmail.cc || [])]
        .map((rcpt) => rcpt.address)
        .filter((address) => !excluded.has(address) && !isUserAddress(address))
      form.value.cc = [...new Set(addresses)]
      showCcField.value = form.value.cc.length > 0
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
    body += convertBody(session.signature, session.editor_format, format)
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
    form.value.to = draft.to.map((rcpt) => rcpt.address)
  }
  if (draft.cc?.length) {
    form.value.cc = draft.cc.map((rcpt) => rcpt.address)
    showCcField.value = true
  }
  if (draft.bcc?.length) {
    form.value.bcc = draft.bcc.map((rcpt) => rcpt.address)
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

  if (result.to?.length) {
    const to = []
    for (const rcpt of result.to) {
      to.push(typeof rcpt === 'string' ? rcpt : rcpt.emails[0].address)
    }
    result.to = to
  }
  if (result.cc?.length) {
    const cc = []
    for (const rcpt of result.cc) {
      cc.push(typeof rcpt === 'string' ? rcpt : rcpt.emails[0].address)
    }
    result.cc = cc
  }
  if (result.bcc?.length) {
    const bcc = []
    for (const rcpt of result.bcc) {
      bcc.push(typeof rcpt === 'string' ? rcpt : rcpt.emails[0].address)
    }
    result.bcc = bcc
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

const getItemTitle = (item) => {
  if (typeof item === 'string') {
    return item
  }
  return item.display_name || `${item.first_name} ${item.last_name}`
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
    attachmentCount.value = session.attachments?.length || 0
    if (draft) {
      initFormFromDraft(session, draft)
    } else {
      initForm(session, originalEmail)
    }
    loading.value = false
  } catch {
    // Already displayed to the user by the API client
  }
}

load()
</script>
