<template>
  <CreationForm
    ref="form"
    :title="$gettext('New provider')"
    :steps="steps"
    :form-getter="getForm"
    :get-v-form-ref="getVFormRef"
    :validate-object="validateProvider"
    :summary-sections="summarySections"
    @close="close"
    @create="submit"
  >
    <template #[`form.general`]>
      <ProviderGeneralForm ref="general" v-model="provider" class="ml-4" />
    </template>
    <template #[`form.associated`]>
      <ProviderAssociatedForm ref="associated" v-model="provider.domains" />
    </template>
  </CreationForm>
</template>

<script setup lang="js">
import { useBusStore, useProvidersStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import CreationForm from '@/components/tools/CreationForm'
import ProviderAssociatedForm from './form_steps/ProviderAssociatedForm.vue'
import ProviderGeneralForm from './form_steps/ProviderGeneralForm.vue'
import { computed, ref } from 'vue'

const emit = defineEmits(['close'])
const { $gettext } = useGettext()
const busStore = useBusStore()
const providersStore = useProvidersStore()

const associatedDomainsSummary = computed(() => {
  const result = []
  let first = true
  for (const domain of provider.value.domains) {
    const value = domain.new_domain
      ? `${domain.name} => ${domain.new_domain.name}`
      : `${domain.name} ${$gettext('(the domain will be created locally)')}`
    result.push({ key: first ? $gettext('Associated domain') : '', value })
    first = false
  }
  return result
})

const summarySections = computed(() => {
  return [
    {
      title: $gettext('General'),
      items: [
        { key: $gettext('Name'), value: provider.value.name },
        { key: $gettext('Address'), value: provider.value.address },
        { key: $gettext('Port'), value: provider.value.port },
        {
          key: $gettext('Secured'),
          value: provider.value.secured,
          type: 'yesno',
        },
      ],
    },
    {
      title: $gettext('Associated domains'),
      items: associatedDomainsSummary.value,
    },
  ]
})

const steps = [
  { name: 'general', title: $gettext('General') },
  { name: 'associated', title: $gettext('Associated domains') },
]

const provider = ref({
  domains: [],
})

// forms ref
const general = ref()
const associated = ref()

const formStepsComponents = { general: general, associated: associated }

initProvider()

function initProvider() {
  provider.value = {
    name: '',
    address: '',
    port: 993,
    secured: true,
    domains: [],
  }
}

function close() {
  initProvider()
  emit('close')
}

function getForm(step) {
  return formStepsComponents.value[step.name]
}

function getVFormRef(step) {
  console.log(provider.value)
  return formStepsComponents[step.name].value.vFormRef
}

function validateProvider() {}

function submit() {
  const data = { ...provider.value }
  data.domains = []
  for (const domain of provider.value.domains) {
    if (domain.new_domain) {
      data.domains.push({
        name: domain.name,
        new_domain: domain.new_domain.pk,
      })
    } else {
      data.domains.push(domain)
    }
  }
  providersStore.createProvider(data).then(() => {
    busStore.displayNotification({ msg: $gettext('Provider created') })
    close()
  })
}
</script>

<style lang="scss">
.highligth {
  background-color: #515d78;
}
</style>
