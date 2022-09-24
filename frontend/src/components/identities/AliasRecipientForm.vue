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
    v-for="(recipient, index) in recipients"
    :key="index"
    class="mr-2 mt-2"
    close
    @click:close="removeRecipient(index)"
    >
    {{ recipient }}
  </v-chip>
</validation-observer>
</template>

<script>
import EmailField from '@/components/tools/EmailField'

export default {
  props: ['value'],
  components: {
    EmailField
  },
  data () {
    return {
      recipient: '',
      recipients: []
    }
  },
  methods: {
    async addRecipient () {
      this.recipients.push(this.recipient)
      this.$emit('input', this.recipients)
      this.$refs.recipientField.reset()
    },
    removeRecipient (index) {
      this.recipients.splice(index, 1)
      this.$emit('input', this.recipients)
    }
  },
  watch: {
    value: {
      handler: function (newValue) {
        if (newValue) {
          this.recipients = [...newValue]
        } else {
          this.recipients = []
        }
      },
      immediate: true
    }
  }
}
</script>
