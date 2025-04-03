<template>
  <div>
    <div
      v-for="mailbox in props.mailboxes"
      :key="mailbox.name"
      class="py-1 pl-3 text-body-2"
    >
      <div
        :class="getBackgroundColorClass(mailbox)"
        class="d-flex mailbox pa-1 align-center"
        @click="$emit('mailboxSelected', mailbox)"
        @mouseover="setHover(mailbox, true)"
        @mouseleave="setHover(mailbox, false)"
      >
        <v-icon :icon="iconByMailboxType[mailbox.type]" class="mr-4" />
        <template v-if="mailbox.unseen > 0">
          <span class="font-weight-bold">
            {{ getMailboxLabel(mailbox) }} ({{ mailbox.unseen }})
          </span>
        </template>
        <template v-else>
          {{ getMailboxLabel(mailbox) }}
        </template>
        <v-spacer />
        <v-btn
          v-if="mailbox.sub"
          :icon="getMailboxState(mailbox) ? 'mdi-minus' : 'mdi-plus'"
          size="xsmall"
          variant="flat"
          color="transparent"
          @click.stop="toggleMailbox(mailbox)"
        />
      </div>
      <MailboxList
        v-if="getMailboxState(mailbox) && mailbox.sub && mailbox.sub.length"
        :mailboxes="mailbox.sub"
        class="mt-1"
        @mailbox-selected="(mailbox) => $emit('mailboxSelected', mailbox)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/webmail'

const route = useRoute()

const props = defineProps({
  mailboxes: {
    type: Array,
    default: null,
  },
})
const emit = defineEmits(['mailboxSelected'])

const iconByMailboxType = {
  inbox: 'mdi-inbox',
  draft: 'mdi-file',
  junk: 'mdi-fire',
  sent: 'mdi-email-fast-outline',
  trash: 'mdi-trash-can-outline',
  normal: 'mdi-folder-outline',
}

const hoverStates = ref({})
const mailboxStates = ref({})

function getMailboxLabel(mailbox) {
  return mailbox.label.split('/').pop()
}

function setHover(mailbox, value) {
  hoverStates.value[mailbox.name] = value
}

function getBackgroundColorClass(mailbox) {
  if (route.query.mailbox === mailbox.name) {
    return 'bg-primary-lighten-1'
  }
  return hoverStates.value[mailbox.name] ? 'bg-primary-lighten-1' : 'bg-primary'
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
      mailbox.sub = resp.data
    })
  }
}
</script>

<style scoped lang="scss">
.mailbox {
  cursor: pointer;
  &:hover {
    border-radius: 5px;
  }
}
</style>
