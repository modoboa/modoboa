<template>
<validation-observer ref="observer">
  <validation-provider
    vid="recipients"
    v-slot="{ errors }"
    >
    <email-field
      ref="recipientField"
      v-model="recipient"
      :placeholder="'Start typing a name here...'|translate"
      @domain-selected="addRecipient"
      :hint="'Alias(es) of this mailbox. To create a catchall alias, just enter the domain name (@domain.tld).'|translate"
      persistent-hint
      allow-add
      :error-messages="errors"
      />
  </validation-provider>
  <v-chip
    v-for="(recipient, index) in alias.recipients"
    :key="index"
    class="mr-2 mt-2"
    close
    @click:close="alias.recipients.splice(index, 1)"
    >
    {{ recipient }}
  </v-chip>
</validation-observer>
</template>

<script>
import EmailField from '@/components/tools/EmailField'

export default {
  props: ['alias'],
  components: {
    EmailField
  },
  data () {
    return {
      recipient: ''
    }
  },
  methods: {
    async addRecipient () {
      this.alias.recipients.push(this.recipient)
      this.$refs.recipientField.reset()
    }
  }
}
</script>
