<template>
<div>
  <v-switch
    :label="'Enable DNS checks' | translate"
    v-model="domain.enable_dns_checks"
    />
  <v-switch
    :label="'Enable DKIM signing' | translate"
    v-model="domain.enable_dkim"
    />
  <v-text-field
    :label="'DKIM key selector' | translate"
    v-model="domain.dkim_key_selector"
    :disabled="!domain.enable_dkim"
    outlined
    />
  <choice-field
    v-model="domain.dkim_key_length"
          :label="'DKIM key length' | translate"
    :choices="dkimKeyLengths"
    :disabled="!domain.enable_dkim"
    />
</div>
</template>

<script>
import ChoiceField from '@/components/tools/ChoiceField'

export default {
  components: {
    ChoiceField
  },
  props: ['domain'],
  data () {
    return {
      dkimKeyLengths: [
        {
          label: '1024',
          value: 1024
        },
        {
          label: '2048',
          value: 2048
        },
        {
          label: '4096',
          value: 4096
        }
      ]
    }
  }
}
</script>
