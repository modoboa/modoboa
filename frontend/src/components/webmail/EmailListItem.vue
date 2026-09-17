<template>
  <v-card
    density="compact"
    class="mb-2 mx-1"
    draggable="true"
    @dragstart="$emit('dragstart', $event, [email.imapid])"
  >
    <v-card-text
      class="d-flex align-center"
      :class="{ 'font-weight-bold': email.style === 'unseen' }"
    >
      <v-checkbox
        v-model="webmailStore.selection"
        :value="email.imapid"
        color="primary"
        hide-details
      />
      <v-btn
        :icon="email.flagged ? 'mdi-star' : 'mdi-star-outline'"
        variant="flat"
        @click="$emit('toggleFollow', email)"
      />
      <v-menu v-if="scheduled" location="bottom">
        <template #activator="{ props: menuProps }">
          <v-btn
            icon="mdi-dots-vertical"
            v-bind="menuProps"
            size="small"
            variant="text"
          >
          </v-btn>
        </template>
        <MenuItems :items="scheduledMessageActions" :obj="email" />
      </v-menu>

      <div class="ml-4 clickable" @click="$emit('open', email.imapid)">
        <div>{{ email.subject }}</div>
        <div class="mt-1 text-grey">
          <EmailAddressList :addresses="addresses" />
        </div>
      </div>
      <v-spacer />
      <div class="text-right">
        <div v-if="!isScheduledDateOver">
          {{ date }}
        </div>
        <div
          v-else
          class="text-error font-weight-bold"
          style="cursor: pointer"
          @click="$emit('schedulingError', email)"
        >
          {{ date }}
        </div>
        <div class="mt-1">
          <v-icon v-if="email.answered" icon="mdi-reply-outline" />
          <v-icon v-if="email.forwarded" icon="mdi-share-outline" />
          <v-icon v-if="email.attachments" icon="mdi-paperclip" />
          <span class="text-grey">{{ $filesize(email.size) }}</span>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { DateTime } from 'luxon'
import { useWebmailStore } from '@/stores'
import EmailAddressList from './EmailAddressList.vue'
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

const addresses = computed(() =>
  props.scheduled ? props.email.recipients : [props.email.from_address]
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

<style lang="scss" scoped>
.v-card-text {
  padding: 0;
}
.clickable {
  cursor: pointer;
}
</style>
