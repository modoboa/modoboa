<template>
  <div>
    <div
      v-for="mailbox in props.mailboxes"
      :key="mailbox.name"
      class="pl-3 text-body-2"
      :class="{ 'py-1': !props.compact }"
    >
      <div
        :class="getBackgroundColorClass(mailbox)"
        class="d-flex mailbox pa-1 align-center"
        @click="updateSelection(mailbox.name)"
        @mouseover="setHover(mailbox, true)"
        @mouseleave="setHover(mailbox, false)"
      >
        <v-icon :icon="iconByMailboxType[mailbox.type]" class="mr-4" />
        <template v-if="mailbox.name === route.query.mailbox">
          <span v-if="currentMailboxUnseen > 0" class="font-weight-bold">
            {{ getMailboxLabel(mailbox) }} ({{
              getCurrentMailboxUnseen(mailbox)
            }})
          </span>
          <span v-else>
            {{ getMailboxLabel(mailbox) }}
          </span>
        </template>
        <template v-else>
          <span v-if="mailbox.unseen > 0" class="font-weight-bold">
            {{ getMailboxLabel(mailbox) }} ({{ mailbox.unseen }})
          </span>
          <span v-else>
            {{ getMailboxLabel(mailbox) }}
          </span>
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
        v-model="model"
        :mailboxes="mailbox.sub"
        class="mt-1"
        :light-mode="props.lightMode"
        :compact="props.compact"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useBusStore } from '@/stores'
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
})
const model = defineModel()
const emit = defineEmits(['update:modelValue'])

const route = useRoute()
const busStore = useBusStore()

const iconByMailboxType = {
  inbox: 'mdi-inbox',
  draft: 'mdi-file',
  junk: 'mdi-fire',
  sent: 'mdi-email-fast-outline',
  trash: 'mdi-trash-can-outline',
  normal: 'mdi-folder-outline',
}

const currentMailboxUnseen = ref(null)
const hoverStates = ref({})
const mailboxStates = ref({})

function getMailboxLabel(mailbox) {
  return mailbox.label.split('/').pop()
}

function getCurrentMailboxUnseen(mailbox) {
  if (currentMailboxUnseen.value === null) {
    currentMailboxUnseen.value = mailbox.unseen
  }
  return currentMailboxUnseen.value
}

function setHover(mailbox, value) {
  hoverStates.value[mailbox.name] = value
}

function getBackgroundColorClass(mailbox) {
  if (model.value === mailbox.name) {
    return `bg-primary-lighten-1`
  }
  if (!props.lightMode) {
    return hoverStates.value[mailbox.name]
      ? `bg-primary-lighten-1`
      : `bg-primary`
  }
  return hoverStates.value[mailbox.name] ? 'bg-primary' : `bg-white`
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

watch(
  () => busStore.mbCounterKey,
  () => {
    api.getUserMailboxUnseen(route.query.mailbox).then((resp) => {
      currentMailboxUnseen.value = resp.data.counter
    })
  }
)
</script>

<style scoped lang="scss">
.mailbox {
  cursor: pointer;
  &:hover {
    border-radius: 5px;
  }
}
</style>
