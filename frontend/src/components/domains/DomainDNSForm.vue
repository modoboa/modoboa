<template>
<div>
  <v-switch
    :label="'Enable DNS checks' | translate"
    v-model="form.enable_dns_checks"
    @input="update"
    />
  <v-switch
    :label="'Enable DKIM signing' | translate"
    v-model="form.enable_dkim"
    @input="update"
    />
  <v-text-field
    :label="'DKIM key selector' | translate"
    v-model="form.dkim_key_selector"
    :disabled="!form.enable_dkim"
    outlined
    @input="update"
    />
  <choice-field
    v-model="form.dkim_key_length"
          :label="'DKIM key length' | translate"
    :choices="dkimKeyLengths"
    :disabled="!form.enable_dkim"
    @input="update"
    />
</div>
</template>

<script>
import ChoiceField from '@/components/tools/ChoiceField'

export default {
  components: {
    ChoiceField
  },
  props: ['value'],
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
      ],
      form: {}
    }
  },
  methods: {
    update () {
      this.$emit('input', this.form)
    }
  },
  watch: {
    value: {
      handler: function (newValue) {
        this.form = { ...newValue }
      },
      immediate: true
    }
  }
}
</script>
