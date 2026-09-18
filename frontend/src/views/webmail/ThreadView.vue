<template>
  <div class="bg-white rounded-lg pa-4 h-100 overflow-y-auto">
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />

      <v-btn-group color="primary" rounded="lg" density="compact" divided>
        <v-btn prepend-icon="mdi-reply" @click="() => replyToLatest()">
          {{ $gettext('Reply') }}
        </v-btn>
        <v-btn size="small" icon>
          <v-icon icon="mdi-chevron-down" />
          <v-menu activator="parent">
            <v-list>
              <v-list-item
                :title="$gettext('Reply all')"
                @click="() => replyToLatest(true)"
              />
              <v-list-item
                :title="$gettext('Forward')"
                @click="forwardLatest"
              />
            </v-list>
          </v-menu>
        </v-btn>
      </v-btn-group>
      <v-btn
        class="ml-2"
        color="error"
        variant="tonal"
        icon="mdi-trash-can"
        size="small"
        :loading="working"
        :title="$gettext('Delete the whole conversation')"
        @click="deleteThread"
      >
      </v-btn>
      <v-btn
        v-if="!isJunkFolder"
        class="ml-2"
        color="warning"
        variant="tonal"
        icon="mdi-fire"
        size="small"
        :loading="working"
        @click="markThreadAsJunk"
      >
      </v-btn>
      <v-btn
        v-else
        class="ml-2"
        color="success"
        variant="tonal"
        icon="mdi-thumb-up"
        size="small"
        :loading="working"
        @click="markThreadAsNotJunk"
      >
      </v-btn>
      <v-spacer />
      <span class="text-grey text-body-small">
        {{ messageCountLabel }}
      </span>
    </v-toolbar>

    <v-skeleton-loader v-if="loading" type="article@2" />
    <template v-else>
      <h2 class="mt-2 mb-4">{{ subject }}</h2>
      <v-expansion-panels v-model="openedPanels" multiple variant="accordion">
        <v-expansion-panel
          v-for="message in messages"
          :key="message.imapid"
          :value="message.imapid"
        >
          <v-expansion-panel-title>
            <div class="d-flex align-center w-100">
              <div
                class="text-truncate"
                :class="{ 'font-weight-bold': message.style === 'unseen' }"
              >
                <EmailAddressList :addresses="[message.from_address]" />
              </div>
              <v-spacer />
              <v-icon
                v-if="message.answered"
                icon="mdi-reply-outline"
                size="small"
                class="mr-1"
              />
              <v-icon
                v-if="message.attachments"
                icon="mdi-paperclip"
                size="small"
                class="mr-1"
              />
              <span class="text-grey text-body-small mr-2">
                {{ message.date }}
              </span>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="d-flex align-center mb-2">
              <v-btn
                size="x-small"
                variant="text"
                prepend-icon="mdi-reply"
                @click="replyTo(message)"
              >
                {{ $gettext('Reply') }}
              </v-btn>
              <v-btn
                size="x-small"
                variant="text"
                prepend-icon="mdi-share-outline"
                @click="forward(message)"
              >
                {{ $gettext('Forward') }}
              </v-btn>
              <v-btn
                size="x-small"
                variant="text"
                prepend-icon="mdi-open-in-new"
                @click="openMessage(message)"
              >
                {{ $gettext('Open') }}
              </v-btn>
            </div>
            <div
              v-if="contents[message.imapid]?.attachments?.length"
              class="mb-2"
            >
              <v-icon icon="mdi-paperclip" />
              <template
                v-for="(attachment, index) in contents[message.imapid]
                  .attachments"
                :key="attachment.name"
              >
                <template v-if="index > 0">, </template>
                <a
                  href="#"
                  @click="
                    downloadAttachment(
                      message.imapid,
                      attachment.name,
                      attachment.partnum
                    )
                  "
                >
                  {{ attachment.name }}
                </a>
              </template>
            </div>
            <v-progress-linear v-if="!contents[message.imapid]" indeterminate />
            <EmailMessageBody
              v-else
              :body="contents[message.imapid].body"
              :enable-images="enableImages"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import { useSpecialFolders } from '@/composables/webmail'
import api from '@/api/webmail'
import EmailAddressList from '@/components/webmail/EmailAddressList.vue'
import EmailMessageBody from '@/components/webmail/EmailMessageBody.vue'

const { $gettext, $ngettext } = useGettext()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const route = useRoute()
const router = useRouter()
const { isJunkFolder } = useSpecialFolders(() => route.query.mailbox)

const enableImages = ref(false)
const loading = ref(true)
const messages = ref([])
const contents = ref({})
const openedPanels = ref([])
const working = ref(false)

const mailbox = computed(() => route.query.mailbox)

const subject = computed(() => messages.value[0]?.subject || '')

const latest = computed(() => messages.value[messages.value.length - 1])

const uids = computed(() => messages.value.map((message) => message.imapid))

const messageCountLabel = computed(() => {
  const count = messages.value.length
  return $ngettext('%{count} message', '%{count} messages', count, { count })
})

const backToMailbox = () => {
  router.push({ name: 'MailboxView', query: { mailbox: mailbox.value } })
}

const close = backToMailbox

const fetchThread = async () => {
  loading.value = true
  let redirecting = false
  try {
    const resp = await api.getThread(mailbox.value, route.query.mailid)
    const results = resp.data.results
    if (results.length <= 1) {
      // The thread lost its other messages, or never had any: show the
      // message itself rather than a conversation of one
      redirecting = true
      router.replace({
        name: 'EmailView',
        query: {
          mailbox: mailbox.value,
          mailid: results[0]?.imapid || route.query.mailid,
        },
      })
      return
    }
    messages.value = results
    // Unread messages and the last one are expanded right away; the
    // watcher below loads what they need
    openedPanels.value = messages.value
      .filter(
        (message, index) =>
          message.style === 'unseen' || index === messages.value.length - 1
      )
      .map((message) => message.imapid)
  } finally {
    // Keep the skeleton until the message view takes over
    if (!redirecting) {
      loading.value = false
    }
  }
}

// Bodies are loaded when a message is expanded, which also marks it as read
const loadContent = async (message) => {
  if (!message || contents.value[message.imapid]) {
    return
  }
  const options = {
    dformat: 'html',
    links: '0',
    images: enableImages.value ? '1' : '0',
  }
  const resp = await api.getEmailContent(mailbox.value, message.imapid, options)
  contents.value[message.imapid] = resp.data
  message.style = undefined
  reloadMailboxCounters()
}

const downloadAttachment = async (mailid, name, part) => {
  const resp = await api.getEmailAttachment(mailbox.value, mailid, part)
  const blob = new Blob([resp.data], { type: resp.headers['Content-Type'] })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = name
  link.click()
  URL.revokeObjectURL(link.href)
}

const openMessage = (message) => {
  router.push({
    name: 'EmailView',
    query: { mailbox: mailbox.value, mailid: message.imapid },
  })
}

const replyTo = (message, all) => {
  const query = { mailbox: mailbox.value, mailid: message.imapid }
  if (all) {
    query.all = all
  }
  router.push({ name: 'ReplyEmailView', query })
}

const replyToLatest = (all) => replyTo(latest.value, all)

const forward = (message) => {
  router.push({
    name: 'ForwardEmailView',
    query: { mailbox: mailbox.value, mailid: message.imapid },
  })
}

const forwardLatest = () => forward(latest.value)

const runOnThread = async (request, message) => {
  working.value = true
  try {
    await request(mailbox.value, uids.value)
    backToMailbox()
    displayNotification({ msg: message })
  } finally {
    working.value = false
  }
}

const deleteThread = () =>
  runOnThread(api.deleteSelection, $gettext('Conversation deleted'))

const markThreadAsJunk = () =>
  runOnThread(api.markSelectionAsJunk, $gettext('Conversation marked as junk'))

const markThreadAsNotJunk = () =>
  runOnThread(
    api.markSelectionAsNotJunk,
    $gettext('Conversation marked as not junk')
  )

// The bodies to load follow the panels that are open, which is the
// model of the accordion itself: one source of truth, whether a panel
// was opened by the reader or expanded on arrival
watch(openedPanels, (imapids) => {
  imapids.forEach((imapid) =>
    loadContent(messages.value.find((message) => message.imapid === imapid))
  )
})

onMounted(fetchThread)
</script>
