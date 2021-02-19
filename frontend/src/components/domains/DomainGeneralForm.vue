<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      :label="'Domain name (ex: domain.tld)' | translate"
      v-model="domain.name"
      :error-messages="errors"
      outlined
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <choice-field v-model="domain.type"
                  :label="'Type' | translate"
                  :choices="domainTypes"
                  :error-messages="errors"
                  />
  </validation-provider>
  <v-switch
    :label="'Enabled' | translate"
    v-model="domain.enabled"
    :hint="'Control if this domain will be allowed to send and receive messages' | translate"
    persistent-hint
    />
</validation-observer>
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
      ]
    }
  }
}
</script>
