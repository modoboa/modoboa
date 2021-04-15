<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      v-model="account.mailbox.full_address"
      :label="'Email' | translate"
      :error-messages="errors"
      :disabled="account.role === 'SimpleUsers'"
      outlined
      />
  </validation-provider>
  <div class="d-flex">
    <v-text-field
      v-model="account.mailbox.quota"
      :label="'Quota' | translate"
      :hint="'Quota for this mailbox, can be expressed in KB, MB (default) or GB. Define a custom value or use domain\'s default one. Leave empty to define an unlimited value (not allowed for domain administrators).' | translate"
      persistent-hint
      class="mr-4 quota"
      :disabled="account.mailbox.use_domain_quota"
      outlined
      />
    <v-switch
      v-model="account.mailbox.use_domain_quota"
      :label="useDomainQuotaLabel"
      />
  </div>
  <v-text-field
    v-model="account.mailbox.message_limit"
    :label="'Message sending limit' | translate"
    :hint="'Number of messages this mailbox can send per day. Leave empty for no limit.' | translate"
    persistent-hint
    outlined
    />
</validation-observer>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: ['account'],
  computed: {
    ...mapGetters({
      getDomainByName: 'identities/getDomainByName'
    }),
    domainQuota () {
      const email = this.account.mailbox.full_address
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
  watch: {
    account: {
      handler (val) {
        if (val.role === 'SimpleUsers') {
          this.$set(val.mailbox, 'full_address', val.username)
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
