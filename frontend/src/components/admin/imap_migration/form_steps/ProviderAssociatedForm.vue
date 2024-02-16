<template>
  <v-form ref="formRef">
    <v-text-field
      ref="initialdomainField"
      v-model="domain.name"
      :placeholder="$gettext('Name of the domain to migrate')"
      variant="outlined"
      density="compact"
      @keydown="onKeyDown"
    />
    <v-autocomplete
      v-model="domain.new_domain"
      :label="$gettext('Local domain (optional)')"
      :items="localDomains"
      item-title="name"
      return-object
      variant="outlined"
      density="compact"
      clearable
      @keydown="onKeyDown"
    />
  </v-form>
  <v-btn icon="mdi-plus" color="primary" @click="addDomain" />
  <v-spacer />
  <v-chip
    v-for="(domain, index) in domains"
    :key="index"
    class="mr-2 mt-2"
    closable
    @click:close="removeDomain(index)"
  >
    <template v-if="domain.new_domain">
      {{ domain.name }} --> {{ domain.new_domain.name }}
    </template>
    <template v-else>
      {{ domain.name }}
    </template>
  </v-chip>

  <v-form ref="vFormRef">
    <v-input :rules="[atLeastOneAssDomain]" />
  </v-form>
</template>

<script setup lang="js">
import domainsApi from '@/api/domains'
import providerApi from '@/api/imap_migration/providers'
import { ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()

const props = defineProps({ modelValue: { type: Array, default: null } })
const emit = defineEmits(['update:modelValue'])
const domains = ref([])

const formRef = ref()
const vFormRef = ref()
const domain = ref({
  name: '',
  new_domain: '',
})
const localDomains = ref([])

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      domains.value = [...value]
    }
  },
  { immediate: true }
)

async function addDomain() {
  const valid = await formRef.value.validate()
  if (!valid) {
    return
  }
  providerApi.checkAssociatedDomain(domain.value).then((response) => {
    if (response.status === 200) {
      domains.value.push({
        name: domain.value.name,
        new_domain: domain.value.new_domain,
      })
      emit('update:modelValue', domains.value)
      domain.value = {
        name: '',
        new_domain: '',
      }
    }
  })
}

function removeDomain(index) {
  domains.value.splice(index, 1)
  emit('update:modelValue', domains.value)
}

function onKeyDown(e) {
  const keyCode = e.keyCode
  if (keyCode === 13 || keyCode === 9) {
    // on enter or tab
    addDomain()
    e.preventDefault()
  }
}

domainsApi.getDomains().then((resp) => {
  localDomains.value = resp.data
})

function atLeastOneAssDomain() {
  if (domains.value.length === 0) {
    return $gettext('You need to bind at least one domain to the provider.')
  }
  return true
}

defineExpose({ vFormRef })
</script>
