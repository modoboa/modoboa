<template>
  <div
    class="mail-row"
    :class="{ unread: email.style === 'unseen', selected: isSelected }"
    draggable="true"
    @dragstart="$emit('dragstart', $event, [email.imapid])"
  >
    <span class="accent" />
    <v-checkbox
      v-model="webmailStore.selection"
      :value="email.imapid"
      class="cell-check"
      color="primary"
      density="compact"
      hide-details
    />
    <v-btn
      :icon="email.flagged ? 'mdi-star' : 'mdi-star-outline'"
      :color="email.flagged ? 'secondary' : 'label'"
      class="cell-icon"
      variant="text"
      size="small"
      density="comfortable"
      :title="$gettext('Follow up')"
      @click="$emit('toggleFollow', email)"
    />
    <v-menu v-if="scheduled" location="bottom">
      <template #activator="{ props: menuProps }">
        <v-btn
          icon="mdi-dots-vertical"
          class="cell-icon"
          v-bind="menuProps"
          variant="text"
          size="small"
          density="comfortable"
        />
      </template>
      <MenuItems :items="scheduledMessageActions" :obj="email" />
    </v-menu>

    <span class="cell-sender" :title="senderTitle">{{ senderName }}</span>
    <span class="cell-subject" @click="$emit('open', email.imapid)">
      {{ email.subject || $gettext('(no subject)') }}
    </span>
    <span class="cell-flags">
      <v-icon v-if="email.answered" icon="mdi-reply-outline" size="small" />
      <v-icon v-if="email.forwarded" icon="mdi-share-outline" size="small" />
      <v-icon v-if="email.attachments" icon="mdi-paperclip" size="small" />
    </span>
    <span
      class="cell-date"
      :class="{ 'text-error font-weight-bold': isScheduledDateOver }"
      :style="isScheduledDateOver ? 'cursor: pointer' : ''"
      @click="isScheduledDateOver && $emit('schedulingError', email)"
    >
      {{ date }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { DateTime } from 'luxon'
import { useWebmailStore } from '@/stores'
import MenuItems from '@/components/tools/MenuItems.vue'

const props = defineProps({
  email: {
    type: Object,
    required: true,
  },
  scheduled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'open',
  'toggleFollow',
  'reschedule',
  'deleteScheduled',
  'schedulingError',
  'dragstart',
])

const { $gettext } = useGettext()
const webmailStore = useWebmailStore()

const isSelected = computed(() =>
  webmailStore.selection.includes(props.email.imapid)
)

// Scheduled messages are listed by recipient: the sender is always you
const addresses = computed(() =>
  props.scheduled ? props.email.recipients || [] : [props.email.from_address]
)

const senderName = computed(() =>
  addresses.value
    .filter(Boolean)
    .map((address) => address.name || address.address)
    .join(', ')
)

const senderTitle = computed(() =>
  addresses.value
    .filter(Boolean)
    .map((address) => address.fulladdress)
    .join(', ')
)

const date = computed(() =>
  props.scheduled ? props.email.scheduled_datetime : props.email.date
)

const isScheduledDateOver = computed(() => {
  if (!props.scheduled || !props.email.scheduled_datetime_raw) return false
  return DateTime.fromISO(props.email.scheduled_datetime_raw) < DateTime.now()
})

const scheduledMessageActions = computed(() => [
  {
    label: $gettext('Reschedule'),
    icon: 'mdi-send-clock-outline',
    onClick: (email) => emit('reschedule', email),
  },
  {
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: (email) => emit('deleteScheduled', email),
    color: 'red',
  },
])
</script>
