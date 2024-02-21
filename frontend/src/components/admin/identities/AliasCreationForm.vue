<template>
  <CreationForm
    ref="form"
    :title="$gettext('New alias')"
    :steps="steps"
    :form-getter="getForm"
    :get-v-form-ref="getVFormRef"
    :validate-object="validateAlias"
    :summary-sections="summarySections"
    @close="close"
    @create="submit"
  >
    <template #[`form.general`]>
      <AliasGeneralForm ref="general" v-model="alias" />
    </template>
    <template #[`form.recipients`]>
      <AliasRecipientForm ref="recipients" v-model="alias.recipients" />
    </template>
  </CreationForm>
</template>

<script setup lang="js">
import { useBusStore, useIdentitiesStore } from '@/stores'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRouter } from 'vue-router'

import aliasesApi from '@/api/aliases'

import AliasGeneralForm from './form_steps/AliasGeneralForm.vue'
import AliasRecipientForm from './form_steps/AliasRecipientForm.vue'
import CreationForm from '@/components/tools/CreationForm.vue'

const { $gettext } = useGettext()
const busStore = useBusStore()
const identitiesStore = useIdentitiesStore()
const router = useRouter()

const emit = defineEmits(['close', 'created'])

//Forms refs
const general = ref()
const recipients = ref()

const formStepsComponenents = {
  general: general,
  recipients: recipients,
}

const summarySections = computed(() => {
  const result = [
    {
      title: $gettext('General'),
      items: [
        {
          key: $gettext('Random address'),
          value: alias.value.random,
          type: 'yesno',
        },
        { key: $gettext('Address'), value: alias.value.address },
      ],
    },
  ]
  if (alias.value.expire_at !== undefined) {
    result[0].items.push({
      key: $gettext('Expire at'),
      value: alias.value.expire_at,
    })
  }
  if (alias.value.description !== undefined) {
    result[0].items.push({
      key: $gettext('Description'),
      value: alias.value.description,
    })
  }
  result.push({
    title: $gettext('Recipients'),
    items: [
      {
        key: $gettext('Recipients'),
        value: alias.value.recipients.join(', '),
      },
    ],
  })
  return result
})

const alias = ref(getInitialForm())

const steps = ref([
  {
    name: 'general',
    title: $gettext('General'),
  },
  {
    name: 'recipients',
    title: $gettext('Recipients'),
  },
])

function close() {
  alias.value = getInitialForm()
  emit('close')
}
function getInitialForm() {
  return {
    random: false,
    enabled: true,
    recipients: [],
  }
}

function getForm(step) {
  return formStepsComponenents.step[step.name]
}

function getVFormRef(step) {
  return formStepsComponenents[step.name].value.vFormRef
}

function validateAlias() {
  const data = { ...alias.value }
  if (data.recipients.length === 0) {
    delete data.recipients
  }
  const validation = aliasesApi.validate(data)
  validation.catch((error) => {
    if (error.response.status === 409 && error.response.data.id !== undefined) {
      busStore.displayNotification({
        msg: $gettext('Alias already exists, redirecting to edit page'),
        type: 'warning',
      })
      router.push({
        name: 'AliasEdit',
        params: { id: error.response.data.id },
      })
    }
  })
  return validation
}

function submit() {
  if (alias.value.domain !== undefined) {
    delete alias.value.domain
  }
  identitiesStore.createIdentity('alias', alias.value).then(() => {
    emit('created')
    close()
  })
}
</script>
