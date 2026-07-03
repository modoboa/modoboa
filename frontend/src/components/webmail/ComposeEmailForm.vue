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
            :title="$gettext('Send')"
            :aria-label="$gettext('Send')"
            @click="submit"
          />
          <v-btn
            v-else
            prepend-icon="mdi-send"
            variant="tonal"
            color="primary"
            :height="btnSize"
            :loading="working"
            :text="$gettext('Send')"
            @click="submit"
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
            item-title="display_name"
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
            item-title="display_name"
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
      <EmailSchedulingForm
        @schedule="scheduleAndSubmit"
        @close="closeSchedulingForm"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import constants from '@/constants.json'
import debounce from 'debounce'
import AttachmentsDialog from '@/components/webmail/AttachmentsDialog'
import BodyEditor from '@/components/webmail/BodyEditor'
import EmailSchedulingForm from '@/components/webmail/EmailSchedulingForm'
import rules from '@/plugins/rules'
import api from '@/api/webmail'
import contactsApi from '@/api/contacts'

const props = defineProps({
  originalEmail: {
    type: Object,
    default: null,
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
const emit = defineEmits(['onToggleHtmlMode'])

const route = useRoute()
const router = useRouter()
// `mobile` (< lg by default) keeps driving touch sizing and fullscreen
// dialogs; `compact` (xs, < 600px) drives the toolbar collapse (icon-only
// Send, overflow kebab). Keying the collapse on `mobile` shrank the toolbar
// on any half-width desktop window — way too early.
const { mobile, xs: compact } = useDisplay()
const { $gettext } = useGettext()
const { displayNotification, reloadData } = useBusStore()
const authStore = useAuthStore()

// 44px touch targets on mobile (WCAG 2.5.8), compact 36px on desktop.
const btnSize = computed(() => (mobile.value ? 44 : 36))

const allowedSenders = ref([])
const attachmentCount = ref(0)
const contacts = ref([])
// IMAP uid of the draft backing this composition. The backend's save action
// deletes the previous draft and pushes a new one, returning the NEW uid —
// it must be threaded into every subsequent save or each save duplicates
// the draft.
const draftMailid = ref(route.query.mailid || null)
const draftSavedAt = ref(null)
const autosaving = ref(false)
const editorMode = ref('plain')
const htmlMode = ref(false)
const form = ref({})
const formRef = ref()
const showAttachmentsDialog = ref(false)
const showCcField = ref(false)
const showBccField = ref(false)
const showSchedulingForm = ref(false)
const working = ref(false)

const close = () => {
  router.push({
    name: 'MailboxView',
  })
}

// The plain/HTML switch lives in the toolbar; reply/forward views listen to
// the emit to refetch the quoted body in the matching format.
const toggleHtmlMode = () => {
  htmlMode.value = !htmlMode.value
  emit('onToggleHtmlMode', htmlMode.value)
}

// Initial mode comes from the user's editor preference (compose session).
watch(editorMode, (value) => {
  htmlMode.value = value === 'html'
})

const initForm = () => {
  form.value = {
    sender: authStore.authUser.username,
    request_dsn: false,
    request_mdn: false,
  }
  if (props.originalEmail) {
    if (!props.forward) {
      // Reply: address the original sender (recipients make no sense when
      // forwarding — the whole point is picking new ones).
      form.value.to = props.originalEmail.reply_to
        ? [props.originalEmail.reply_to]
        : [props.originalEmail.from_address.address]
      if (props.replyAll) {
        let addresses = props.originalEmail.to
          .filter((rcpt) => rcpt.address !== authStore.authUser.username)
          .map((rcpt) => rcpt.fulladdress)
        if (props.originalEmail.cc && props.originalEmail.cc.length) {
          addresses = addresses.concat(
            props.originalEmail.cc.map((rcpt) => rcpt.fulladdress)
          )
        }
        form.value.cc = addresses
        showCcField.value = true
      }
      if (props.originalEmail.message_id) {
        form.value.in_reply_to = props.originalEmail.message_id
      }
    }
    form.value.subject = props.originalEmail.subject
    form.value.body = props.originalEmail.body
  }
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
  if (draftMailid.value) {
    result.mailid = draftMailid.value
  }
  return result
}

const submit = async (reload) => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const body = prepareMessage()
  try {
    await api.sendEmailFromComposeSession(route.query.uid, body)
    // The message went out: drop the backing draft (autosaved or manually
    // saved), otherwise every sent email leaves a stale copy in Drafts.
    if (draftMailid.value) {
      api
        .deleteSelection(constants.DRAFTS_FOLDER, [draftMailid.value])
        .catch(() => {})
    }
    router.push({ name: 'MailboxView' })
    const msg = body.scheduled_datetime
      ? $gettext('Email scheduled')
      : $gettext('Email sent')
    if (reload) {
      reloadData()
    }
    displayNotification({ msg })
  } catch (error) {
    console.log(error)
  } finally {
    working.value = false
  }
}

const scheduleAndSubmit = async (datetime) => {
  form.value.scheduled_datetime = datetime
  await submit(true)
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

const initialize = async (body) => {
  if (route.params.mailbox === constants.DRAFTS_FOLDER && route.query.mailid) {
    // Load draft
    const draft = await api.getEmailContent(
      constants.DRAFTS_FOLDER,
      route.query.mailid
    )
    form.value.sender = draft.data.from_address.address
    if (draft.data.to?.length) {
      form.value.to = draft.data.to.map((rcpt) => rcpt.address)
    }
    if (draft.data.cc?.length) {
      form.value.cc = draft.data.cc.map((rcpt) => rcpt.address)
      showCcField.value = true
    }
    if (draft.data.bcc?.length) {
      form.value.bcc = draft.data.bcc.map((rcpt) => rcpt.address)
      showBccField.value = true
    }
    if (draft.data.subject) {
      form.value.subject = draft.data.subject
    }
    if (draft.data.body) {
      form.value.body = draft.data.body
    }
  } else if (body.signature) {
    if (form.value.body) {
      form.value.body += body.signature
    } else {
      form.value.body = body.signature
    }
  }
  editorMode.value = body.editor_format
  // Baseline for autosave: whatever the form holds after initial population
  // (loaded draft, reply quote, signature) is "already saved" — only real
  // user edits from here on trigger a save.
  lastSavedSnapshot = draftSnapshot()
}

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
  const snapshot = draftSnapshot()
  if (snapshot === lastSavedSnapshot) {
    return
  }
  autosaving.value = true
  try {
    const body = prepareMessage()
    const resp = await api.saveComposeSession(route.query.uid, body)
    // Thread the new uid into the next save, or every save duplicates the
    // draft server-side.
    if (resp?.data?.mailid) {
      draftMailid.value = resp.data.mailid
    }
    lastSavedSnapshot = snapshot
    draftSavedAt.value = new Date().toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    console.log(error)
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

const getItemTitle = (item) => {
  if (typeof item === 'string') {
    return item
  }
  return item.display_name || `${item.first_name} ${item.last_name}`
}

watch(
  () => props.originalEmail,
  () => {
    initForm()
  },
  { immediate: true }
)

if (!route.query.uid) {
  const args =
    route.query.mailbox === constants.DRAFTS_FOLDER ? [route.query.mailid] : []
  api.createComposeSession(...args).then((resp) => {
    const query = { ...route.query, uid: resp.data.uid }
    attachmentCount.value = resp.data.attachments?.length || 0
    router.push({ name: route.name, query })
    initialize(resp.data)
  })
} else {
  api.getComposeSession(route.query.uid).then((resp) => {
    attachmentCount.value = resp.data.attachments.length
    initialize(resp.data)
  })
}

api.getAllowedSenders().then((resp) => {
  allowedSenders.value = resp.data
})
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
