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
    </v-col>
    <v-col cols="6">
      <account-resources
        v-if="account.resources && account.resources.length"
        :account="account"
        />
      <account-aliases v-if="account.aliases" class="mt-2" :account="account" />
    </v-col>
  </v-row>
  <v-row v-if="account.role === 'DomainAdmins'">
    <v-col cols="6">
      <domain-admin-domains :account="account" />
    </v-col>
  </v-row>
</div>
</template>

<script>
import accounts from '@/api/accounts'
import AccountAliases from '@/components/identities/AccountAliases'
import AccountResources from '@/components/identities/AccountResources'
import AccountSummary from '@/components/identities/AccountSummary'
import DomainAdminDomains from '@/components/identities/DomainAdminDomains'

export default {
  components: {
    AccountAliases,
    AccountResources,
    AccountSummary,
    DomainAdminDomains
  },
  data () {
    return {
      account: { pk: this.$route.params.id }
    }
  },
  mounted () {
    accounts.get(this.$route.params.id).then(resp => {
      this.account = resp.data
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
