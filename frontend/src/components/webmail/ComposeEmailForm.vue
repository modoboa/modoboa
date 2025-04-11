<template>
  <div
    class="bg-white rounded-lg pa-4 position-relative h-100 d-flex flex-column"
  >
    <v-toolbar color="white">
      <v-btn icon="mdi-arrow-left" size="small" variant="flat" @click="close" />
      <v-btn
        class="ml-2"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-send"
        :loading="working"
        :text="$gettext('Send')"
        @click="submit"
      >
      </v-btn>
    </v-toolbar>
    <v-form ref="formRef" class="flex-grow-1 d-flex flex-column">
      <div>
        <v-row class="align-center">
          <v-col cols="2">
            <span>{{ $gettext('From') }}</span>
          </v-col>
          <v-col cols="8">
            <v-select
              v-model="form.sender"
              :items="validSenderAddresses"
              variant="outlined"
              density="compact"
              hide-details="auto"
              :rules="[rules.required]"
            />
          </v-col>
        </v-row>
        <v-row class="align-center">
          <v-col cols="2">
            <span>{{ $gettext('To') }}</span>
          </v-col>
          <v-col cols="8">
            <v-text-field
              v-model="form.to"
              :placeholder="$gettext('Provide one or more addresses')"
              variant="outlined"
              density="compact"
              hide-details="auto"
              :rules="[rules.required]"
            />
          </v-col>
          <v-col cols="2">
            <v-btn
              v-if="!showCcField"
              :text="$gettext('Cc')"
              prepend-icon="mdi-plus"
              size="x-small"
              variant="flat"
              @click="showCcField = true"
            />
            <v-btn
              v-if="!showBccField"
              :text="$gettext('Bcc')"
              prepend-icon="mdi-plus"
              size="x-small"
              variant="flat"
              @click="showBccField = true"
            />
          </v-col>
        </v-row>
        <v-row v-if="showCcField" class="align-center">
          <v-col cols="2">
            <span>{{ $gettext('Cc') }}</span>
            <v-btn
              icon="mdi-close"
              variant="flat"
              size="x-small"
              @click="showCcField = false"
            />
          </v-col>
          <v-col cols="8">
            <v-text-field
              v-model="form.cc"
              :placeholder="$gettext('Provide one or more addresses')"
              variant="outlined"
              density="compact"
              hide-details="auto"
            />
          </v-col>
        </v-row>
        <v-row v-if="showBccField" class="align-center">
          <v-col cols="2">
            <span>{{ $gettext('Bcc') }}</span>
            <v-btn
              icon="mdi-close"
              variant="flat"
              size="x-small"
              @click="showBccField = false"
            />
          </v-col>
          <v-col cols="8">
            <v-text-field
              v-model="form.bcc"
              :placeholder="$gettext('Provide one or more addresses')"
              variant="outlined"
              density="compact"
              hide-details="auto"
            />
          </v-col>
        </v-row>
        <v-row class="align-center">
          <v-col cols="2">
            <span>{{ $gettext('Subject') }}</span>
          </v-col>
          <v-col cols="8">
            <v-text-field
              v-model="form.subject"
              variant="outlined"
              density="compact"
              hide-details="auto"
            />
          </v-col>
        </v-row>
      </div>
      <HtmlEditor
        v-model="form.body"
        class="d-flex flex-column flex-grow-1 mt-4"
      />
    </v-form>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore, useBusStore } from '@/stores'
import HtmlEditor from '@/components/tools/HtmlEditor'
import rules from '@/plugins/rules'
import api from '@/api/webmail'

const props = defineProps({
  originalEmail: {
    type: Object,
    default: null,
  },
})

const router = useRouter()
const { $gettext } = useGettext()
const { displayNotification } = useBusStore()
const authStore = useAuthStore()

const form = ref({})
const formRef = ref()
const showCcField = ref(false)
const showBccField = ref(false)
const working = ref(false)

const validSenderAddresses = computed(() => {
  return [authStore.authUser.username]
})

const close = () => {
  router.push({
    name: 'MailboxView',
  })
}

const initForm = () => {
  form.value = {
    sender: authStore.authUser.username,
  }
  console.log(props.originalEmail)
  if (props.originalEmail) {
    form.value.to = props.originalEmail.from_address.address
    form.value.subject = props.originalEmail.subject
    form.value.body = props.originalEmail.body
  }
}

const submit = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const body = { ...form.value }
  body.to = [body.to]
  try {
    await api.sendEmail(body)
    router.push({ name: 'MailboxView' })
    displayNotification({ msg: $gettext('Email sent') })
  } catch (error) {
    console.log(error)
  } finally {
    working.value = false
  }
}

watch(
  () => props.originalEmail,
  () => {
    initForm()
  },
  { immediate: true }
)
</script>
