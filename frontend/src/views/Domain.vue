<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Domain</translate> {{ domain.name }}</v-toolbar-title>
    <v-btn color="primary" icon @click="showEditForm = true"><v-icon>mdi-circle-edit-outline</v-icon></v-btn>
    <v-btn icon @click="showAdminList = true" :title="'Show administrator list'|translate">
      <v-icon>mdi-account-supervisor</v-icon>
    </v-btn>
  </v-toolbar>
  <v-layout>
    <v-row>
      <v-col cols="6">
        <domain-summary :domain="domain" />
        <div class="mt-4" />
        <domain-dns-summary :domain="domain" />
      </v-col>
    </v-row>
  </v-layout>
  <v-dialog v-model="showEditForm"
            persistent
            max-width="800px"
            >
    <domain-form :domain="domain" @close="showEditForm = false" />
  </v-dialog>
  <v-dialog v-model="showAdminList"
            persistent
            max-width="800px"
            >
    <administrator-list
      :domain="domain"
      @close="showAdminList = false"
      />
  </v-dialog>
</div>
</template>

<script>
import domains from '@/api/domains'
import AdministratorList from '@/components/domains/AdministratorList'
import DomainForm from '@/components/domains/DomainForm'
import DomainDNSSummary from '@/components/domains/DomainDNSSummary'
import DomainSummary from '@/components/domains/DomainSummary'

export default {
  components: {
    AdministratorList,
    DomainForm,
    'domain-dns-summary': DomainDNSSummary,
    DomainSummary
  },
  data () {
    return {
      domain: {},
      showEditForm: false,
      showAdminList: false
    }
  },
  mounted () {
    domains.getDomain(this.$route.params.id).then(resp => {
      this.domain = resp.data
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
