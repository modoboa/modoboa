<template>
<validation-observer ref="observer">
  <label class="m-label">{{ $gettext('Quota') }}</label>
  <v-switch
    v-model="form.mailbox.use_domain_quota"
    :label="useDomainQuotaLabel"
    @change="update"
    />
  <validation-provider
    v-if="!form.mailbox.use_domain_quota"
    v-slot="{ errors }"
    rules=""
    vid="quota"
    >
    <v-text-field
      v-model="form.mailbox.quota"
      :placeholder="'Ex: 10MB. Leave empty for no limit'|translate"
      :hint="'Quota for this mailbox, can be expressed in KB, MB (default) or GB. Define a custom value or use domain\'s default one. Leave empty to define an unlimited value (not allowed for domain administrators).' | translate"
      persistent-hint
      outlined
      :error-messages="errors"
      dense
      @input="update"
      />
  </validation-provider>
  <label class="m-label">{{ $gettext('Daily message sending limit') }}</label>
  <v-text-field
    v-model="form.mailbox.message_limit"
    :placeholder="'Leave empty for no limit' | translate"
    :hint="'Number of messages this mailbox can send per day. Leave empty for no limit.' | translate"
    persistent-hint
    outlined
    dense
    @input="update"
    />
</validation-observer>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: ['value'],
  data () {
    return {
      form: {
        mailbox: {}
      }
    }
  },
  computed: {
    ...mapGetters({
      getDomainByName: 'identities/getDomainByName'
    }),
    domainQuota () {
      const email = this.form.mailbox.full_address
      if (email && email.indexOf('@') !== -1) {
        const domain = this.getDomainByName(email.split('@')[1])
        if (domain) {
          return parseInt(domain.default_mailbox_quota)
        }
      }
      return undefined
    },
    useDomainQuotaLabel () {
      let result = this.$gettext('Use domain default value')
      if (this.domainQuota !== undefined) {
        if (this.domainQuota === 0) {
          result += ` (${this.$gettext('unlimited')})`
        } else {
          result += ` (${this.domainQuota} MB)`
        }
      }
      return result
    }
  },
  methods: {
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
        this.form = { ...newValue }
        if (this.form.role === 'SimpleUsers') {
          this.$set(this.form.mailbox, 'full_address', this.form.username)
        }
      },
      deep: true
    }
  }
}
</script>

<style lang="scss" scoped>
.quota {
  max-width: 50%;
}
</style>
