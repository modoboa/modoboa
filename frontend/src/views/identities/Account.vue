<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Account</translate> {{ account.username }}</v-toolbar-title>
    <v-btn color="primary" icon :to="{ name: 'AccountEdit', params: { id: account.pk } }">
      <v-icon>mdi-circle-edit-outline</v-icon>
    </v-btn>
  </v-toolbar>
  <v-row>
    <v-col cols="6">
      <account-summary :account="account" />
      <domain-admin-domains
        v-if="account.role === 'DomainAdmins'"
        class="mt-2"
        :account="account"
        />

    </v-col>
    <v-col cols="6">
      <resources
        v-if="limitsConfig.params && limitsConfig.params.enable_admin_limits && account.role !== 'SimpleUsers' && account.role !== 'SuperAdmins'"
        :resources="account.resources"
        />
      <account-aliases v-if="account.aliases" class="mt-2" :account="account" />
      <account-sender-addresses
        v-if="account.mailbox"
        class="mt-2"
        :account="account"
        />
    </v-col>
  </v-row>
</div>
</template>

<script>
import accounts from '@/api/accounts'
import AccountAliases from '@/components/identities/AccountAliases'
import AccountSenderAddresses from '@/components/identities/AccountSenderAddresses'
import AccountSummary from '@/components/identities/AccountSummary'
import DomainAdminDomains from '@/components/identities/DomainAdminDomains'
import parameters from '@/api/parameters'
import Resources from '@/components/tools/Resources'

export default {
  components: {
    AccountAliases,
    AccountSenderAddresses,
    AccountSummary,
    DomainAdminDomains,
    Resources
  },
  data () {
    return {
      account: { pk: this.$route.params.id },
      limitsConfig: {}
    }
  },
  mounted () {
    accounts.get(this.$route.params.id).then(resp => {
      this.account = resp.data
    })
    parameters.getApplication('limits').then(resp => {
      this.limitsConfig = resp.data
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
