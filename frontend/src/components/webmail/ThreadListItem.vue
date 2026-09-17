<template>
  <div
    class="mail-row"
    :class="{ unread: thread.unseen_count > 0, selected: isSelected }"
    draggable="true"
    @dragstart="$emit('dragstart', $event, thread.uids)"
  >
    <span class="accent" />
    <v-checkbox
      v-model="selected"
      class="cell-check"
      color="primary"
      density="compact"
      hide-details
    />
    <v-btn
      :icon="thread.flagged ? 'mdi-star' : 'mdi-star-outline'"
      :color="thread.flagged ? 'secondary' : 'label'"
      class="cell-icon"
      variant="text"
      size="small"
      density="comfortable"
      :title="$gettext('Follow up')"
      @click="$emit('toggleFollow', thread.latest)"
    />

    <span class="cell-sender" :title="participantsTitle">
      {{ participantsLabel }}
    </span>
    <span
      v-if="thread.count > 1"
      class="cell-count"
      :title="$gettext('Show the messages of this conversation')"
      @click="toggleExpanded"
    >
      {{ expanded ? '▾' : '▸' }}{{ thread.count }}
    </span>
    <span class="cell-subject" @click="$emit('openThread', thread.root)">
      {{ thread.subject || $gettext('(no subject)') }}
    </span>
    <span class="cell-flags">
      <v-icon
        v-if="thread.latest.answered"
        icon="mdi-reply-outline"
        size="small"
      />
      <v-icon v-if="thread.attachments" icon="mdi-paperclip" size="small" />
    </span>
    <span class="cell-date">{{ thread.latest.date }}</span>
  </div>
  <template v-if="expanded">
    <div
      v-for="message in messages"
      :key="message.imapid"
      class="mail-row mail-row-child"
      :class="{ unread: message.style === 'unseen' }"
      @click="$emit('open', message.imapid)"
    >
      <span class="cell-sender">{{ senderName(message) }}</span>
      <span class="cell-subject">{{ message.subject }}</span>
      <span class="cell-flags">
        <v-icon v-if="message.attachments" icon="mdi-paperclip" size="small" />
      </span>
      <span class="cell-date">{{ message.date }}</span>
    </div>
  </template>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useWebmailStore } from '@/stores'
import api from '@/api/webmail'

const props = defineProps({
  thread: {
    type: Object,
    required: true,
  },
  mailbox: {
    type: String,
    required: true,
  },
})

defineEmits(['open', 'openThread', 'toggleFollow', 'dragstart'])

const { $gettext } = useGettext()
const webmailStore = useWebmailStore()

const expanded = ref(false)
const messages = ref([])

const senderName = (message) =>
  message.from_address?.name || message.from_address?.address || ''

// Only the first participants are named: the column is narrow and the
// point is to recognize the conversation, not to list everyone
const participantsLabel = computed(() => {
  const names = props.thread.participants.map(
    (address) => address.name || address.address
  )
  if (names.length <= 2) {
    return names.join(', ')
  }
  return `${names.slice(0, 2).join(', ')} +${names.length - 2}`
})

const participantsTitle = computed(() =>
  props.thread.participants.map((address) => address.fulladdress).join(', ')
)

const isSelected = computed(() =>
  props.thread.uids.some((uid) => webmailStore.selection.includes(uid))
)

// Selecting a conversation selects all its messages, so that the
// existing bulk actions apply to the whole thread
const selected = computed({
  get() {
    return props.thread.uids.every((uid) =>
      webmailStore.selection.includes(uid)
    )
  },
  set(value) {
    if (value) {
      const missing = props.thread.uids.filter(
        (uid) => !webmailStore.selection.includes(uid)
      )
      webmailStore.selection = [...webmailStore.selection, ...missing]
    } else {
      webmailStore.selection = webmailStore.selection.filter(
        (uid) => !props.thread.uids.includes(uid)
      )
    }
  },
})

const toggleExpanded = async () => {
  if (expanded.value) {
    expanded.value = false
    return
  }
  if (!messages.value.length) {
    const resp = await api.getThread(props.mailbox, props.thread.root)
    messages.value = resp.data.results
  }
  expanded.value = true
}
</script>
