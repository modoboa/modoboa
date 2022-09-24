<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      :label="'Domain name (ex: domain.tld)' | translate"
      v-model="form.name"
      :error-messages="errors"
      outlined
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <choice-field v-model="form.type"
                  :label="'Type' | translate"
                  :choices="domainTypes"
                  :error-messages="errors"
                  @input="update"
                  />
  </validation-provider>
  <v-switch
    :label="'Enabled' | translate"
    v-model="form.enabled"
    :hint="'Control if this domain will be allowed to send and receive messages' | translate"
    persistent-hint
    @change="update"
    />
</validation-observer>
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
      domainTypes: [
        {
          label: 'Domain',
          icon: 'mdi-earth',
          value: 'domain'
        },
        {
          label: 'Relay domain',
          icon: 'mdi-earth',
          value: 'relaydomain'
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
