<template>
  <v-form ref="vFormRef">
    <div>
      <v-switch
        v-model="domain.enable_dns_checks"
        :label="$gettext('Enable DNS checks')"
        color="primary"
      />
      <v-switch
        v-model="domain.enable_dkim"
        :label="$gettext('Enable DKIM signing')"
        color="primary"
      />
      <v-text-field
        v-model="domain.dkim_key_selector"
        :label="$gettext('DKIM key selector')"
        :disabled="!domain.enable_dkim"
        variant="outlined"
      />
      <ChoiceField
        v-model="domain.dkim_key_length"
        :label="$gettext('DKIM key length')"
        :choices="dkimKeyLengths"
        :disabled="!domain.enable_dkim"
      />
    </div>
  </v-form>
</template>

<script setup lang="js">
import ChoiceField from '@/components/tools/ChoiceField'
import { useGettext } from 'vue3-gettext'
import { ref, computed } from 'vue'

const { $gettext } = useGettext()

const props = defineProps({ modelValue: { type: Object, default: () => {} } })

const vFormRef = ref()

const domain = computed(() => props.modelValue)

const dkimKeyLengths = ref([
  {
    label: '1024',
    value: 1024,
  },
  {
    label: '2048',
    value: 2048,
  },
  {
    label: '4096',
    value: 4096,
  },
])

defineExpose({ vFormRef })
</script>
