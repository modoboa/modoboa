<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Domain</translate> {{ domain.name }}</v-toolbar-title>
    <v-btn color="primary" icon :to="{ name: 'DomainEdit', params: { id: domain.pk } }">
      <v-icon>mdi-circle-edit-outline</v-icon>
    </v-btn>
  </v-toolbar>
  <v-layout>
    <v-row>
      <v-col cols="6">
        <domain-summary :domain="domain" />
        <div class="mt-4" />
        <administrator-list
          :domain="domain"
          />
      </v-col>
      <v-col cols="6">
        <dns-detail v-model="domain" />
        <div class="mt-4" />
        <resources
          v-if="limitsConfig.params && limitsConfig.params.enable_domain_limits && domain.resources && domain.resources.length"
          :resources="domain.resources"
          />
      </v-col>
    </v-row>
  </v-layout>
  <v-layout>
    <v-row class="mt-2">
      <v-col cols="12">
        <time-serie-chart :domain="domain" graphic-set="mailtraffic" graphic-name="averagetraffic" />
      </v-col>
      <v-col cols="12">
        <time-serie-chart :domain="domain" graphic-set="mailtraffic" graphic-name="averagetrafficsize" />
      </v-col>
    </v-row>
  </v-layout>
  <v-dialog v-model="showEditForm"
            persistent
            max-width="800px"
            >
    <domain-form :domain="domain" @close="showEditForm = false" />
  </v-dialog>
</div>
</template>

<script>
import domains from '@/api/domains'
import AdministratorList from '@/components/domains/AdministratorList'
import DNSDetail from '@/components/domains/DNSDetail'
import DomainForm from '@/components/domains/DomainForm'
import DomainSummary from '@/components/domains/DomainSummary'
import parameters from '@/api/parameters'
import Resources from '@/components/tools/Resources'
import TimeSerieChart from '@/components/tools/TimeSerieChart'

export default {
  components: {
    AdministratorList,
    'dns-detail': DNSDetail,
    DomainForm,
    DomainSummary,
    Resources,
    TimeSerieChart
  },
  data () {
    return {
      domain: { pk: this.$route.params.id },
      limitsConfig: {},
      showEditForm: false,
      showAdminList: false
    }
  },
  methods: {
  },
  mounted () {
    parameters.getApplication('limits').then(resp => {
      this.limitsConfig = resp.data
    })
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
