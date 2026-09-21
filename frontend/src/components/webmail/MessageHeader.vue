<template>
  <div
    class="message-header"
    :class="{ 'message-header-compact': !showSender }"
  >
    <v-avatar
      v-if="showSender"
      class="message-avatar"
      color="primary"
      variant="tonal"
      size="36"
      aria-hidden="true"
    >
      {{ initials }}
    </v-avatar>
    <div class="message-header-main">
      <div v-if="showSender" class="message-sender-line">
        <AddressButton :address="message.from_address" strong />
        <span v-if="message.from_address.name" class="message-sender-address">
          {{ message.from_address.address }}
        </span>
        <span class="message-date" :title="message.date_full">
          {{ message.date }}
        </span>
      </div>

      <div
        v-for="row in recipientRows"
        :key="row.key"
        class="message-recipients"
      >
        <span class="message-recipients-label">{{ row.label }}</span>
        <div class="message-recipients-list">
          <AddressButton
            v-for="(rcpt, index) in visible(row)"
            :key="`${row.key}-${index}`"
            :address="rcpt"
          />
          <v-btn
            v-if="hiddenCount(row)"
            class="address-button"
            variant="text"
            size="small"
            color="primary"
            @click="expanded[row.key] = true"
          >
            {{
              $gettext('+%{count} more', {
                count: hiddenCount(row),
              })
            }}
          </v-btn>
        </div>
      </div>

      <AttachmentList
        :attachments="message.attachments || []"
        @download="$emit('download', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useGettext } from 'vue3-gettext'
import AddressButton from '@/components/webmail/AddressButton.vue'
import AttachmentList from '@/components/webmail/AttachmentList.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  // In a conversation, the title of the panel already names the
  // sender and the date
  showSender: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['download'])

const { $gettext } = useGettext()

// Past this many recipients, a row folds the others behind a count
const MAX_VISIBLE = 3

const expanded = reactive({})

const initials = computed(() => {
  const { name, address } = props.message.from_address
  const words = (name || address || '?')
    .replace(/[<>"']/g, '')
    .split(/[\s@._-]+/)
    .filter(Boolean)
  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
})

const recipientRows = computed(() => {
  const message = props.message
  const rows = [
    { key: 'to', label: $gettext('To'), addresses: message.to },
    { key: 'cc', label: $gettext('Cc'), addresses: message.cc },
    { key: 'bcc', label: $gettext('Bcc'), addresses: message.bcc },
  ]
  // Only worth a row when answers go somewhere else than the sender
  const replyTo = (message.reply_to || []).filter(
    (address) =>
      address.address?.toLowerCase() !==
      message.from_address?.address?.toLowerCase()
  )
  rows.push({
    key: 'reply_to',
    label: $gettext('Reply to'),
    addresses: replyTo,
  })
  return rows.filter((row) => row.addresses?.length)
})

// One more hidden name is not worth a "+1": show it instead
const visible = (row) =>
  expanded[row.key] || row.addresses.length <= MAX_VISIBLE + 1
    ? row.addresses
    : row.addresses.slice(0, MAX_VISIBLE)

const hiddenCount = (row) => row.addresses.length - visible(row).length
</script>
