<template>
  <v-form ref="vFormRef">
    <label class="m-label">{{ $gettext('Quota') }}</label>
    <v-switch
      v-model="form.mailbox.use_domain_quota"
      :label="useDomainQuotaLabel"
      color="primary"
      @update:model-value="cleanQuota"
    />
    <v-text-field
      v-if="!form.mailbox.use_domain_quota"
      v-model="form.mailbox.quota"
      :placeholder="$gettext('Ex: 10MB. Leave empty for no limit')"
      :hint="
        $gettext(
          'Quota for this mailbox, can be expressed in KB, MB (default) or GB. Define a custom value or use domain\'s default one. Leave empty to define an unlimited value (not allowed for domain administrators).'
        )
      "
      persistent-hint
      variant="outlined"
      density="compact"
    />
    <label class="m-label">{{ $gettext('Daily message sending limit') }}</label>
    <v-text-field
      v-model="form.mailbox.message_limit"
      :placeholder="$gettext('Leave empty for no limit')"
      :hint="
        $gettext(
          'Number of messages this mailbox can send per day. Leave empty for no limit.'
        )
      "
      persistent-hint
      variant="outlined"
      density="compact"
      :rules="[rules.numericOrNull]"
      @update:model-value="cleanMessageLimit"
    />
    <v-switch
      v-model="form.mailbox.is_send_only"
      :label="$gettext('Send only account')"
      density="compact"
      color="primary"
    />
  </v-form>
</template>

<script setup lang="js">
import { ref, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useDomainsStore } from '@/stores'
import rules from '@/plugins/rules'

const { $gettext } = useGettext()
const emit = defineEmits(['update:modelValue'])
const props = defineProps({ modelValue: { type: Object, default: null } })
const domainsStore = useDomainsStore()

const vFormRef = ref()
const form = ref({
  mailbox: {},
})

watch(
  props.modelValue,
  (value) => {
    if (value) {
      form.value = { ...value }
      if (form.value.role === 'SimpleUsers') {
        if (!form.value.mailbox) {
          form.value.mailbox = {}
        }
        form.value.mailbox.full_address = form.value.username
      }
      if (form.value.mailbox.message_limit === '') {
        form.value.mailbox.message_limit = null
      }
    } else {
      form.value = {
        mailbox: {},
      }
    }
  },
  { immediate: true }
)

watch(
  form,
  (value) => {
    emit('update:modelValue', value)
  },
  { deep: true }
)

const domainQuota = computed(() => {
  const email = form.value.mailbox.full_address
  if (email && email.indexOf('@') !== -1) {
    const domain = domainsStore.getDomainByName(email.split('@')[1])
    if (domain) {
      return parseInt(domain.default_mailbox_quota)
    }
  }
  return undefined
})

const useDomainQuotaLabel = computed(() => {
  let result = $gettext('Use domain default value')
  if (domainQuota.value !== undefined) {
    if (domainQuota.value === 0) {
      result += ` (${$gettext('unlimited')})`
    } else {
      result += ` (${domainQuota.value} MB)`
    }
  }
  return result
})

function cleanQuota(value) {
  if (value) {
    delete form.value.mailbox.quota
  }
}

function cleanMessageLimit(value) {
  if (value === '') {
    delete form.value.mailbox.message_limit
  }
}

defineExpose({ vFormRef })
</script>

<style lang="scss" scoped>
.quota {
  max-width: 50%;
}
</style>
