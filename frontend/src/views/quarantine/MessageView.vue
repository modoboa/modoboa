<template>
  <div class="bg-white rounded-lg pa-4 position-relative h-100">
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />
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
      <v-btn class="ml-2" variant="tonal" icon size="small">
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
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import api from '@/api/amavis'

const route = useRoute()
const router = useRouter()
const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const fullHeaders = ref(null)
const loading = ref(false)
const message = ref(null)

const headers = computed(() => {
  if (!fullHeaders.value) {
    return message.value.headers
  }
  return fullHeaders.value
})

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
    const resp = await api.getMessageHeaders(route.params.mailid)
    fullHeaders.value = resp.data.headers
  } finally {
    loading.value = false
  }
}

const releaseMessage = async () => {
  loading.value = true
  const data = {
    selection: [{ rcpt: route.rcpt, mailid: route.mailid }],
  }
  try {
    const resp = await api.releaseSelection(data)
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
    selection: [{ rcpt: route.params.rcpt, mailid: route.params.mailid }],
  }
  try {
    await api.deleteSelection(data)
    displayNotification({ msg: $gettext('Message deleted') })
    router.push({ name: 'QuarantineView' })
  } finally {
    loading.value = false
  }
}

const mark = async (mtype, msg) => {
  loading.value = true
  const data = {
    type: mtype,
    selection: [{ rcpt: route.params.rcpt, mailid: route.params.mailid }],
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

const resp = await api.getMessageContent(route.params.mailid)
message.value = resp.data
</script>
