<template>
  <div
    class="bg-white rounded-lg pa-4 position-relative h-100 d-flex flex-column"
  >
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />
      <v-btn
        class="ml-2"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-send"
        :loading="working"
        :text="$gettext('Send')"
        @click="submit"
      >
      </v-btn>
      <v-btn
        class="ml-2"
        variant="tonal"
        prepend-icon="mdi-paperclip"
        :text="$gettext('Attachments') + ` (${attachmentCount})`"
        @click="openAttachmentsDialog"
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
              item-title="display_name"
              return-object
              :placeholder="$gettext('Provide one or more addresses')"
              variant="outlined"
              density="compact"
              hide-details="auto"
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
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import debounce from 'debounce'
import AttachmentsDialog from '@/components/webmail/AttachmentsDialog'
import BodyEditor from '@/components/webmail/BodyEditor'
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
const { displayNotification } = useBusStore()
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
      ? props.originalEmail.reply_to
      : props.originalEmail.from_address.address
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

const submit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const body = { ...form.value }
  if (typeof form.value.to !== 'string') {
    body.to = [form.value.to.emails[0].address]
  } else {
    body.to = [form.value.to]
  }
  if (body.cc?.length) {
    const cc = []
    for (const rcpt of body.cc) {
      cc.push(typeof rcpt === 'string' ? rcpt : rcpt.emails[0].address)
    }
    body.cc = cc
  }
  if (body.bcc?.length) {
    const bcc = []
    for (const rcpt of body.bcc) {
      bcc.push(typeof rcpt === 'string' ? rcpt : rcpt.emails[0].address)
    }
    body.bcc = bcc
  }
  try {
    await api.sendEmailFromComposeSession(route.query.uid, body)
    router.push({ name: 'MailboxView' })
    displayNotification({ msg: $gettext('Email sent') })
  } catch (error) {
    console.log(error)
  } finally {
    working.value = false
  }
}

const openAttachmentsDialog = () => {
  showAttachmentsDialog.value = true
}

const closeAttachmentDialog = async () => {
  showAttachmentsDialog.value = false
  const resp = await api.getUploadedAttachments(route.query.uid)
  attachmentCount.value = resp.data.length
}

const lookForContacts = debounce(async (search) => {
  if (search) {
    const params = { search }
    const resp = await contactsApi.getContacts(params)
    if (resp.data.length) {
      contacts.value = resp.data
    }
  } else {
    contacts.value = []
  }
}, 500)

const initialize = (body) => {
  if (body.signature) {
    if (form.value.body) {
      form.value.body += body.signature
    } else {
      form.value.body = body.signature
    }
  }
  editorMode.value = body.editor_format
}

watch(
  () => props.originalEmail,
  () => {
    initForm()
  },
  { immediate: true }
)

if (!route.query.uid) {
  api.createComposeSession().then((resp) => {
    const query = { ...route.query, uid: resp.data.uid }
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
