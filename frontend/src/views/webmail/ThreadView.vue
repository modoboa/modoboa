<template>
  <div class="bg-white rounded-lg pa-4 h-100 overflow-y-auto">
    <v-toolbar
      class="mail-header"
      color="surface"
      flat
      :height="48"
      :extension-height="40"
    >
      <v-btn
        icon="mdi-arrow-left"
        variant="text"
        size="small"
        :title="$gettext('Back to the mailbox')"
        @click="close"
      />
      <h2 class="mail-subject" :title="subject">{{ subject }}</h2>
      <span class="mail-header-meta">{{ messageCountLabel }}</span>
      <template #extension>
        <v-btn
          variant="text"
          size="small"
          prepend-icon="mdi-reply"
          @click="() => replyToLatest()"
        >
          {{ $gettext('Reply') }}
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          prepend-icon="mdi-reply-all"
          @click="() => replyToLatest(true)"
        >
          {{ $gettext('Reply all') }}
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          prepend-icon="mdi-share-outline"
          @click="forwardLatest"
        >
          {{ $gettext('Forward') }}
        </v-btn>
        <span class="mail-header-separator" />
        <v-btn
          icon="mdi-trash-can-outline"
          color="error"
          variant="text"
          size="small"
          :loading="working"
          :title="$gettext('Delete the whole conversation')"
          @click="deleteThread"
        />
        <v-btn
          v-if="!isJunkFolder"
          icon="mdi-fire"
          color="warning"
          variant="text"
          size="small"
          :loading="working"
          :title="$gettext('Mark the conversation as junk')"
          @click="markThreadAsJunk"
        />
        <v-btn
          v-else
          icon="mdi-thumb-up-outline"
          color="success"
          variant="text"
          size="small"
          :loading="working"
          :title="$gettext('Mark the conversation as not junk')"
          @click="markThreadAsNotJunk"
        />
      </template>
    </v-toolbar>

    <v-skeleton-loader v-if="loading" type="article@2" />
    <template v-else>
      <v-expansion-panels
        v-model="openedPanels"
        class="thread-panels"
        multiple
        variant="accordion"
        elevation="0"
      >
        <v-expansion-panel
          v-for="message in messages"
          :key="message.imapid"
          :value="message.imapid"
        >
          <v-expansion-panel-title>
            <span
              class="thread-sender"
              :class="{ 'font-weight-bold': message.style === 'unseen' }"
              :title="message.from_address?.fulladdress"
            >
              {{ senderName(message) }}
            </span>
            <span
              v-if="message.attachments"
              class="thread-attachment"
              :title="attachmentTitle(message)"
            >
              <v-icon icon="mdi-paperclip" size="small" />
              <span class="thread-attachment-name">
                {{ attachmentFirstName(message) }}
              </span>
              <span
                v-if="attachmentOthers(message)"
                class="thread-attachment-count"
              >
                +{{ attachmentOthers(message) }}
              </span>
            </span>
            <span class="thread-flags">
              <v-icon
                v-if="message.answered"
                icon="mdi-reply-outline"
                size="small"
              />
            </span>
            <span class="thread-date">{{ message.date }}</span>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="thread-message-actions">
              <v-btn
                size="small"
                variant="text"
                prepend-icon="mdi-reply"
                @click="replyTo(message)"
              >
                {{ $gettext('Reply') }}
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                prepend-icon="mdi-reply-all"
                @click="replyTo(message, true)"
              >
                {{ $gettext('Reply all') }}
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                prepend-icon="mdi-share-outline"
                @click="forward(message)"
              >
                {{ $gettext('Forward') }}
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                prepend-icon="mdi-open-in-new"
                @click="openMessage(message)"
              >
                {{ $gettext('Open') }}
              </v-btn>
            </div>
            <v-progress-linear v-if="!contents[message.imapid]" indeterminate />
            <template v-else>
              <MessageHeader
                :message="contents[message.imapid]"
                :show-sender="false"
                class="mb-3"
                @download="
                  (attachment) => downloadAttachment(message.imapid, attachment)
                "
              />
              <RemoteContentBanner
                v-if="
                  contents[message.imapid].remote_content_blocked &&
                  !imagesEnabled[message.imapid]
                "
                @show="showImages(message)"
              />
              <EmailMessageBody
                :body="contents[message.imapid].body"
                :enable-images="!!imagesEnabled[message.imapid]"
              />
            </template>
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
import { downloadBlob } from '@/utils'
import EmailMessageBody from '@/components/webmail/EmailMessageBody.vue'
import MessageHeader from '@/components/webmail/MessageHeader.vue'
import RemoteContentBanner from '@/components/webmail/RemoteContentBanner.vue'

const { $gettext, $ngettext } = useGettext()
const { displayNotification, reloadMailboxCounters } = useBusStore()
const route = useRoute()
const router = useRouter()
const { isJunkFolder } = useSpecialFolders(() => route.query.mailbox)

// Messages whose remote images the reader asked for, by IMAP id
const imagesEnabled = ref({})
const loading = ref(true)
const messages = ref([])
const contents = ref({})
const openedPanels = ref([])
const working = ref(false)

const mailbox = computed(() => route.query.mailbox)

// A collapsed message names its first file and counts the others:
// enough to find what one came for without opening every message. The
// count is kept out of the truncated name, so it never disappears.
const attachmentFirstName = (message) =>
  (message.attachment_list || [])[0]?.name || ''

const attachmentOthers = (message) =>
  Math.max((message.attachment_list || []).length - 1, 0)

const attachmentTitle = (message) =>
  (message.attachment_list || []).map((file) => file.name).join(', ')

const senderName = (message) =>
  message.from_address?.name || message.from_address?.address || ''

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
const loadContent = async (message, reload = false) => {
  if (!message || (contents.value[message.imapid] && !reload)) {
    return
  }
  const options = {
    dformat: 'html',
    links: '0',
    images: imagesEnabled.value[message.imapid] ? '1' : '0',
  }
  const resp = await api.getEmailContent(mailbox.value, message.imapid, options)
  contents.value[message.imapid] = resp.data
  message.style = undefined
  reloadMailboxCounters()
}

// The body is loaded again: the server only keeps the remote images
// when asked to
const showImages = (message) => {
  imagesEnabled.value[message.imapid] = true
  loadContent(message, true)
}

const downloadAttachment = async (mailid, attachment) => {
  const resp = await api.getEmailAttachment(
    mailbox.value,
    mailid,
    attachment.partnum
  )
  // Axios lowercases header names
  const type =
    resp.headers['content-type'] ||
    attachment.content_type ||
    'application/octet-stream'
  downloadBlob(new Blob([resp.data], { type }), attachment.name)
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
