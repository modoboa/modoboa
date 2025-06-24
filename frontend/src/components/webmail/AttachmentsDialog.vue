<template>
  <v-card>
    <v-card-title>{{ $gettext('Attachments') }}</v-card-title>
    <v-card-text>
      <v-form ref="formRef">
        <v-file-input
          v-model="file"
          density="compact"
          variant="outlined"
          :rules="[rules.required]"
        />
        <div class="w-100 d-flex justify-center">
          <v-btn
            color="primary"
            variant="tonal"
            :text="$gettext('Attach')"
            @click="submit"
          />
        </div>
      </v-form>

      <v-table class="mt-4 border-sm">
        <tbody>
          <tr v-for="attachment in attachments" :key="attachment.fname">
            <td>{{ attachment.fname }}</td>
            <td>
              <v-btn
                icon="mdi-trash-can"
                color="error"
                size="small"
                variant="text"
                @click="removeAttachment(attachment)"
              />
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn :text="$gettext('Close')" variant="flat" @click="close" />
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api/webmail'
import rules from '@/plugins/rules'

const props = defineProps({
  sessionUid: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close'])

const attachments = ref([])
const file = ref()
const formRef = ref()
const loading = ref(false)

const close = () => {
  emit('close')
}

const submit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  const formData = new FormData()
  formData.append('attachment', file.value)
  loading.value = true
  try {
    const resp = await api.uploadAttachment(props.sessionUid, formData)
    attachments.value.push(resp.data)
    formRef.value.reset()
  } finally {
    loading.value = false
  }
}

const removeAttachment = async (attachment) => {
  await api.removeAttachment(props.sessionUid, attachment.tmpname)
  const index = attachments.value.findIndex(
    (item) => item.tmpname === attachment.tmpname
  )
  attachments.value.splice(index, 1)
}

api.getComposeSession(props.sessionUid).then((resp) => {
  attachments.value = resp.data.attachments
})
</script>
