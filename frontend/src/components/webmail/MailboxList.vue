<template>
  <v-list density="compact" class="pa-0 bg-transparent">
    <div
      v-for="mailbox in props.mailboxes"
      :key="mailbox.name"
      class="mailbox-wrapper"
    >
      <v-list-item
        :active="model === mailbox.name"
        :prepend-icon="iconByMailboxType[mailbox.type]"
        class="mailbox text-body-2"
        link
        @click="updateSelection(mailbox.name)"
        @mouseover="setHover(mailbox, true)"
        @mouseleave="setHover(mailbox, false)"
        @dragover.prevent
        @dragenter="setHover(mailbox, true)"
        @dragleave="setHover(mailbox, false)"
        @drop.prevent="onDrop(mailbox)"
      >
        <v-list-item-title v-if="!props.rail">
          <span :class="{ 'font-weight-bold': mailboxUnseen(mailbox) > 0 }">
            {{ getMailboxLabel(mailbox) }} {{ mailboxCountLabel(mailbox) }}
          </span>
        </v-list-item-title>

        <template #append v-if="!props.rail && mailbox.sub">
          <v-btn
            :icon="getMailboxState(mailbox) ? 'mdi-minus' : 'mdi-plus'"
            size="x-small"
            variant="flat"
            color="transparent"
            :aria-label="
              getMailboxState(mailbox)
                ? $gettext('Collapse folder')
                : $gettext('Expand folder')
            "
            @click.stop="toggleMailbox(mailbox)"
          />
        </template>
      </v-list-item>

      <div class="pl-4" v-if="getMailboxState(mailbox) && mailbox.sub && mailbox.sub.length">
        <MailboxList
          v-model="model"
          :mailboxes="mailbox.sub"
          class="mt-1"
          :light-mode="props.lightMode"
          :compact="props.compact"
        />
      </div>
    </div>
  </v-list>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useWebmailStore } from '@/stores'
import api from '@/api/webmail'

const props = defineProps({
  mailboxes: {
    type: Array,
    default: null,
  },
  lightMode: {
    type: Boolean,
    default: false,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  unseenCounters: {
    type: Boolean,
    default: true,
  },
  allowUnselect: {
    type: Boolean,
    default: false,
  },
  rail: {
    type: Boolean,
    default: false,
  },
})
const model = defineModel()
const emit = defineEmits(['update:modelValue'])

const route = useRoute()
const { $gettext } = useGettext()
const busStore = useBusStore()
const webmailStore = useWebmailStore()

const iconByMailboxType = {
  inbox: 'mdi-inbox',
  draft: 'mdi-file',
  junk: 'mdi-alert-octagon-outline',
  sent: 'mdi-email-fast-outline',
  scheduled: 'mdi-send-clock-outline',
  trash: 'mdi-trash-can-outline',
  normal: 'mdi-folder-outline',
}

const hoverStates = ref({})
const mailboxStates = ref({})

function getMailboxLabel(mailbox) {
  return mailbox.label.split('/').pop()
}

function mailboxUnseen(mailbox) {
  // Unseen counts come straight from the folder listing, which WebmailLayout
  // reloads (real per-folder STATUS) on every counter bump. Don't keep a
  // separate "current mailbox" override: it leaked one folder's unseen onto
  // whatever folder matched the route (e.g. Trash showing INBOX's unseen).
  return mailbox.unseen || 0
}

function mailboxCountLabel(mailbox) {
  // Always show the total; prefix with unseen when there are unread messages.
  const total = mailbox.nbmessages || 0
  const unseen = mailboxUnseen(mailbox)
  return unseen > 0 ? `(${unseen}/${total})` : `(${total})`
}

function setHover(mailbox, value) {
  hoverStates.value[mailbox.name] = value
}

function getMailboxState(mailbox) {
  return mailboxStates.value[mailbox.name]
}

function toggleMailbox(mailbox) {
  if (!mailboxStates.value[mailbox.name]) {
    mailboxStates.value[mailbox.name] = false
  }
  mailboxStates.value[mailbox.name] = !mailboxStates.value[mailbox.name]
  if (mailboxStates.value[mailbox.name] && !mailbox.sub.length) {
    api.getUserMailboxes(mailbox.name).then((resp) => {
      mailbox.sub = resp.data.mailboxes
    })
  }
}

function updateSelection(value) {
  if (props.allowUnselect && value === model.value) {
    emit('update:modelValue', null)
  } else {
    emit('update:modelValue', value)
  }
}

async function onDrop(mailbox) {
  try {
    busStore.displayNotification({
      msg: $gettext('Moving selection...'),
      type: 'info',
      timeout: 0,
    })
    const resp = await api.moveSelection(
      route.query.mailbox || 'INBOX',
      mailbox.name,
      webmailStore.selection
    )
    webmailStore.listingKey++
    webmailStore.selection = []
    busStore.reloadMailboxCounters()
  } finally {
    busStore.hideNotification()
  }
}
</script>

<style scoped lang="scss">
.mailbox {
  cursor: pointer;
}
:deep(.v-list-item__spacer) {
  width: 12px !important;
}
:deep(.v-list-item-title) {
  font-size: 0.875rem !important;
}
</style>
