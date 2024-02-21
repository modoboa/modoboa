<template>
  <v-form ref="vFormRef">
    <EmailField
      ref="recipientField"
      v-model="recipient"
      :placeholder="$gettext('Start typing a name here...')"
      :hint="
        $gettext(
          'Alias(es) of this mailbox. To create a catchall alias, just enter the domain name (@domain.tld).'
        )
      "
      persistent-hint
      allow-add
      :rules="requiredRecipient"
      @domain-selected="addRecipient"
    />
    <v-chip
      v-for="(_recipient, index) in recipients"
      :key="index"
      class="mr-2 mt-2"
      closable
      @click:close="removeRecipient(index)"
    >
      {{ _recipient }}
    </v-chip>
  </v-form>
</template>

<script setup lang="js">
import EmailField from '@/components/tools/EmailField'
import { useGettext } from 'vue3-gettext'
import { ref, computed } from 'vue'

const { $gettext } = useGettext()
const emit = defineEmits(['update:model-value'])
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})

const recipients = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:model-value', value),
})

const recipient = ref('')
const recipientField = ref()
const vFormRef = ref()

async function addRecipient() {
  recipients.value.push(recipient.value)
  recipient.value = ''
  vFormRef.value.resetValidation()
}

function removeRecipient(index) {
  recipients.value.splice(index, 1)
}

const requiredRecipient = [
  () =>
    recipients.value.length > 0 ||
    $gettext('Please add at least one recipient.'),
]

defineExpose({ vFormRef })
</script>
