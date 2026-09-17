<template>
  <v-card
    density="compact"
    class="mb-2 mx-1"
    draggable="true"
    @dragstart="$emit('dragstart', $event, thread.uids)"
  >
    <v-card-text
      class="d-flex align-center"
      :class="{ 'font-weight-bold': thread.unseen_count > 0 }"
    >
      <v-checkbox v-model="selected" color="primary" hide-details />
      <v-btn
        :icon="thread.flagged ? 'mdi-star' : 'mdi-star-outline'"
        variant="flat"
        @click="$emit('toggleFollow', thread.latest)"
      />
      <v-btn
        v-if="thread.count > 1"
        :icon="expanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"
        variant="text"
        size="small"
        :loading="loadingMessages"
        :title="$gettext('Show the messages of this conversation')"
        @click="toggleExpanded"
      />
      <div v-else class="expand-placeholder" />

      <div class="ml-4 clickable" @click="$emit('openThread', thread.root)">
        <div>
          {{ thread.subject }}
          <v-chip v-if="thread.count > 1" size="x-small" class="ml-2">
            {{ thread.count }}
          </v-chip>
        </div>
        <div class="mt-1 text-grey">
          <EmailAddressList :addresses="thread.participants" />
        </div>
      </div>
      <v-spacer />
      <div class="text-right">
        <div>{{ thread.latest.date }}</div>
        <div class="mt-1">
          <v-icon v-if="thread.latest.answered" icon="mdi-reply-outline" />
          <v-icon v-if="thread.latest.forwarded" icon="mdi-share-outline" />
          <v-icon v-if="thread.attachments" icon="mdi-paperclip" />
          <span v-if="thread.unseen_count" class="text-primary ml-1">
            {{ thread.unseen_count }} {{ $gettext('unread') }}
          </span>
        </div>
      </div>
    </v-card-text>
    <template v-if="expanded">
      <v-divider />
      <div
        v-for="message in messages"
        :key="message.imapid"
        class="thread-message d-flex align-center clickable"
        :class="{ 'font-weight-bold': message.style === 'unseen' }"
        @click="$emit('open', message.imapid)"
      >
        <div class="text-truncate">
          <EmailAddressList :addresses="[message.from_address]" />
        </div>
        <v-spacer />
        <div class="text-grey ml-4">
          <v-icon
            v-if="message.attachments"
            icon="mdi-paperclip"
            size="small"
          />
          {{ message.date }}
        </div>
      </div>
    </template>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useWebmailStore } from '@/stores'
import EmailAddressList from './EmailAddressList.vue'
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
const loadingMessages = ref(false)
const messages = ref([])

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
    loadingMessages.value = true
    try {
      const resp = await api.getThread(props.mailbox, props.thread.root)
      messages.value = resp.data.results
    } finally {
      loadingMessages.value = false
    }
  }
  expanded.value = true
}
</script>

<style lang="scss" scoped>
.v-card-text {
  padding: 0;
}
.clickable {
  cursor: pointer;
}
.expand-placeholder {
  width: 40px;
}
.thread-message {
  padding: 8px 16px 8px 100px;
  font-size: 0.9rem;
}
.thread-message:hover {
  background-color: rgb(var(--v-theme-surface-light));
}
</style>
