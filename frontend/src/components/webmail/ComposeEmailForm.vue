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
            :loading="working"
            :text="$gettext('Send')"
            @click="submit"
          >
          </v-btn>
          <v-btn size="small" icon>
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

        <v-btn
          class="ml-2"
          variant="tonal"
          prepend-icon="mdi-paperclip"
          :text="$gettext('Attachments') + ` (${attachmentCount})`"
          @click="openAttachmentsDialog"
        />
        <v-btn
          class="ml-2"
          icon="mdi-content-save-outline"
          size="small"
          :title="$gettext('Save as draft')"
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
        <BodyEditor
          v-model="form.body"
          :editor-mode="editorMode"
          @on-toggle-html-mode="(value) => emit('onToggleHtmlMode', value)"
        />
      </v-form>
    </div>
    <v-dialog v-model="showAttachmentsDialog" max-width="800">
      <AttachmentsDialog
        :session-uid="route.query.uid"
        @close="closeAttachmentDialog"
      />
    </v-dialog>
    <v-dialog v-model="showSchedulingForm" max-width="800">
      <EmailSchedulingForm
        @schedule="scheduleAndSubmit"
        @close="closeSchedulingForm"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
})
const emit = defineEmits(['onToggleHtmlMode'])

const route = useRoute()
const router = useRouter()
const { $gettext } = useGettext()
const { displayNotification, reloadData } = useBusStore()
const authStore = useAuthStore()

const allowedSenders = ref([])
const attachmentCount = ref(0)
const contacts = ref([])
const editorMode = ref('plain')
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

const initForm = () => {
  form.value = {
    sender: authStore.authUser.username,
  }
  if (props.originalEmail) {
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
    form.value.subject = props.originalEmail.subject
    form.value.body = props.originalEmail.body
    if (props.originalEmail.message_id) {
      form.value.in_reply_to = props.originalEmail.message_id
    }
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
  if (route.query.mailid) {
    result.mailid = route.query.mailid
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

const saveDraft = async () => {
  working.value = true
  const body = prepareMessage()
  try {
    await api.saveComposeSession(route.query.uid, body)
  } catch (error) {
    console.log(error)
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
  console.log(args)
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
