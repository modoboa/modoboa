<template>
  <v-card :title="title">
    <v-card-text>
      <v-form ref="formRef">
        <v-text-field
          v-model="form.name"
          :label="$gettext('Name')"
          variant="outlined"
          density="compact"
          :rules="[rules.required]"
        />
        <div class="mb-2 rounded-lg">
          <h4>{{ $gettext('Parent mailbox') }}</h4>
          <MailboxList
            v-model="form.parent_mailbox"
            :active-mailbox="props.parent"
            :mailboxes="props.userMailboxes"
            light-mode
            compact
            :unseen-counters="false"
            allow-unselect
          />
        </div>
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn
        :text="$gettext('Close')"
        variant="flat"
        :loading="loading"
        @click="close"
      />
      <v-btn
        :text="submitLabel"
        variant="tonal"
        color="primary"
        :loading="loading"
        @click="submit"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import MailboxList from '@/components/webmail/MailboxList.vue'
import api from '@/api/webmail'
import rules from '@/plugins/rules'

const props = defineProps({
  userMailboxes: Array,
  mailbox: {
    type: String,
    default: null,
  },
  hdelimiter: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close', 'mailboxRenamed'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const form = ref({})
const formRef = ref()
const loading = ref(false)

const title = computed(() => {
  return !props.mailbox
    ? $gettext('Create new mailbox')
    : $gettext('Edit mailbox')
})
const submitLabel = computed(() => {
  return !props.mailbox ? $gettext('Create') : $gettext('Update')
})

const close = () => {
  form.value = {}
  emit('close')
}

const submit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  loading.value = true
  try {
    const body = { ...form.value }
    if (props.mailbox) {
      body.oldname = props.mailbox
      await api.renameUserMailbox(body)
      displayNotification({ msg: $gettext('Mailbox renamed') })
      emit(
        'mailboxRenamed',
        `${body.parent_mailbox}${props.hdelimiter}${body.name}`
      )
    } else {
      await api.createUserMailbox(body)
      displayNotification({ msg: $gettext('Mailbox created') })
    }
    close()
  } finally {
    loading.value = false
  }
}

watch(
  () => props.mailbox,
  (value) => {
    if (value) {
      const parts = props.mailbox.split(props.hdelimiter)
      form.value.name = parts.slice(-1)[0]
      form.value.parent_mailbox = parts.slice(0, -1).join(props.hdelimiter)
    } else {
      form.value = {}
    }
  },
  { immediate: true }
)
</script>
