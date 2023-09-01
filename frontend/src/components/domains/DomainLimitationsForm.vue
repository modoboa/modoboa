<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      :label="'Quota' | translate"
      :hint="'Quota shared between mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
      persistent-hint
      v-model="form.quota"
      :error-messages="errors"
      class="mb-4"
      outlined
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      :label="'Default mailbox quota' | translate"
      :hint="'Default quota applied to mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
      persistent-hint
      v-model="form.default_mailbox_quota"
      :error-messages="errors"
      class="mb-4"
      outlined
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="numeric"
    >
    <v-text-field
      :label="'Message sending limit' | translate"
      :hint="'Number of messages this domain can send per day. Leave empty for no limit.' | translate"
      persistent-hint
      v-model="form.message_limit"
      :error-messages="errors"
      outlined
      @input="update"
      />
  </validation-provider>
</validation-observer>
</template>

<script>
export default {
  props: ['value'],
  data () {
    return {
      form: {}
    }
  },
  methods: {
    reset () {
      this.form = {}
    },
    update () {
      this.$emit('input', this.form)
    }
  },
  mounted () {
    this.form = { ...this.value }
  },
  watch: {
    value: {
      handler (newValue) {
        if (newValue.message_limit === '') {
          newValue.message_limit = null
        }
        this.form = { ...newValue }
      },
      deep: true
    }
  }
}
</script>
