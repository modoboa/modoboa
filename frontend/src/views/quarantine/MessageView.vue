<template>
  <div>
    <div class="text-h5 ml-4">
      {{ $gettext('Quarantined message') }}
    </div>
    <div class="bg-white rounded-lg pa-4 position-relative mt-6 h-100">
      <v-toolbar color="white">
        <v-btn
          v-if="!selfServiceMode"
          icon="mdi-arrow-left"
          size="small"
          variant="flat"
          @click="close"
        />
        <v-btn
          class="ml-2"
          color="success"
          variant="tonal"
          icon="mdi-check"
          size="small"
          :title="$gettext('Release message')"
          :loading="loading"
          @click="releaseMessage"
        >
        </v-btn>
        <v-btn
          class="ml-2"
          color="error"
          variant="tonal"
          icon="mdi-trash-can"
          size="small"
          :title="$gettext('Delete message')"
          :loading="loading"
          @click="deleteMessage"
        >
        </v-btn>
        <template v-if="!selfServiceMode">
          <v-btn
            v-if="manualLearningEnabled"
            class="ml-2"
            variant="tonal"
            icon
            size="small"
          >
            <v-icon icon="mdi-cog" />
            <v-menu activator="parent">
              <v-list density="compact">
                <v-list-item
                  :title="$gettext('Mark as spam')"
                  @click="markAsSpam"
                />
                <v-list-item
                  :title="$gettext('Mark as non-spam')"
                  @click="markAsHam"
                />
              </v-list>
            </v-menu>
          </v-btn>
        </template>
        <v-btn
          class="ml-2"
          variant="tonal"
          size="small"
          :loading="loading"
          @click="toggleFullHeaders"
        >
          <span v-if="!fullHeaders">
            {{ $gettext('View full headers') }}
          </span>
          <span v-else>
            {{ $gettext('Hide full headers') }}
          </span>
        </v-btn>
      </v-toolbar>
      <v-alert
        v-if="message.qtype"
        :title="message.qtype"
        :text="message.qreason"
        type="error"
        variant="tonal"
        class="mb-4"
        density="compact"
      />

      <div class="pa-4 bg-grey-lighten-3 rounded">
        <v-row v-for="header in headers" :key="header.name" no-gutters>
          <v-col cols="2" class="font-weight-bold">
            {{ header.name }}
          </v-col>
          <v-col cols="10">{{ header.value }}</v-col>
        </v-row>
      </div>
      <div class="mt-4" v-html="message.body" />
    </div>
    <ConfirmDialog ref="learningRecipientRef">
      <v-radio-group v-model="learningDatabase" class="mt-4" hide-details>
        <v-radio
          v-for="lrcpt in learningRecipients"
          :key="lrcpt.value"
          :value="lrcpt.value"
          :label="lrcpt.title"
        >
        </v-radio>
      </v-radio-group>
    </ConfirmDialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import { useAmavis } from '@/composables/amavis'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import api from '@/api/amavis'
import constants from '@/constants'

const route = useRoute()
const router = useRouter()
const { $gettext } = useGettext()
const authStore = useAuthStore()
const { displayNotification } = useBusStore()

const fullHeaders = ref(null)
const learningDatabase = ref(null)
const learningRecipientRef = ref(null)
const loading = ref(false)
const message = ref(null)

const headers = computed(() => {
  if (!fullHeaders.value) {
    return message.value.headers
  }
  return fullHeaders.value
})

const selfServiceMode = computed(() => {
  return route.query?.secret_id !== undefined
})
if (selfServiceMode.value) {
  const manualLearningEnabled = ref(false)
} else {
  const { manualLearningEnabled } = await useAmavis()
}

const close = () => {
  router.go(-1)
}

const toggleFullHeaders = async () => {
  if (fullHeaders.value) {
    fullHeaders.value = null
    return
  }
  loading.value = true
  try {
    const resp = await api.getMessageHeaders(
      route.params.mailid,
      route.params.rcpt,
      route.query.secret_id
    )
    fullHeaders.value = resp.data.headers
  } finally {
    loading.value = false
  }
}

const releaseMessage = async () => {
  loading.value = true
  const data = {
    rcpt: route.params.rcpt,
    mailid: route.params.mailid,
  }
  if (selfServiceMode.value) {
    data.secret_id = route.query.secret_id
  }
  try {
    const resp = await api.releaseMessage(route.params.mailid, data)
    if (resp.data.status === 'pending') {
      displayNotification({ msg: $gettext('Release request sent') })
    } else {
      displayNotification({ msg: $gettext('Message released') })
    }
  } finally {
    loading.value = false
  }
}

const deleteMessage = async () => {
  loading.value = true
  const data = {
    rcpt: route.params.rcpt,
    mailid: route.params.mailid,
  }
  if (selfServiceMode.value) {
    data.secret_id = route.query.secret_id
  }
  try {
    await api.deleteMessage(route.params.mailid, data)
    displayNotification({ msg: $gettext('Message deleted') })
    if (!selfServiceMode.value) {
      router.push({ name: 'QuarantineView' })
    }
  } finally {
    loading.value = false
  }
}

const mark = async (mtype, msg) => {
  if (
    manualLearningEnabled.value &&
    authStore.authUser.role !== constants.USER
  ) {
    learningDatabase.value =
      authStore.authUser.role === constants.SUPER_ADMIN ? 'global' : 'domain'
    await learningRecipientRef.value.open(
      $gettext('Learning database'),
      $gettext('Which database should be used for this learning:'),
      { width: 600, noconfirm: true }
    )
  }

  loading.value = true
  const data = {
    type: mtype,
    selection: [{ rcpt: route.params.rcpt, mailid: route.params.mailid }],
  }
  if (learningDatabase.value) {
    data.database = learningDatabase.value
  }
  try {
    await api.markMessageSelection(data)
    displayNotification({ msg })
  } finally {
    loading.value = false
  }
}

const markAsSpam = async () => {
  await mark('spam', $gettext('Message marked as spam'))
}

const markAsHam = async () => {
  await mark('ham', $gettext('Message marked as non-spam'))
}

const resp = await api.getMessageContent(
  route.params.mailid,
  route.params.rcpt,
  route.query.secret_id
)
message.value = resp.data
</script>
