<template>
<v-card>
  <v-card-title>
    <span class="headline">DNS</span>
    <v-btn icon :title="'DNS configuration help'|translate" @click="showConfigHelp = true">
      <v-icon>mdi-information-outline</v-icon>
    </v-btn>
  </v-card-title>

  <v-card-text>
    <v-row>
      <v-col cols="6"><translate>Status</translate></v-col>
      <v-col cols="6">
        <dns-status-chip :status="domain.dns_global_status" @click="showDetail = true" />
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6"><translate>DKIM key</translate></v-col>
      <v-col cols="6">
        <div v-if="domain.dkim_public_key">
          <v-btn color="primary" small>
            <translate>Show key</translate>
          </v-btn>
          <v-btn icon><v-icon>mdi-refresh</v-icon></v-btn>
        </div>
        <translate v-else>Not generated</translate>
      </v-col>
    </v-row>
  </v-card-text>

  <v-dialog v-model="showConfigHelp"
            max-width="800px"
            persistent
            >
    <domain-dns-config :domain="domain" @close="showConfigHelp = false" />
  </v-dialog>
  <v-dialog v-model="showDetail"
            persistent
            max-width="800px">
    <dns-detail @close="showDetail = false" :domain="domain" />
  </v-dialog>
</v-card>
</template>

<script>
import DomainDNSConfig from './DomainDNSConfig'
import DNSDetail from './DNSDetail'
import DNSStatusChip from './DNSStatusChip'

export default {
  components: {
    'dns-detail': DNSDetail,
    'dns-status-chip': DNSStatusChip,
    'domain-dns-config': DomainDNSConfig
  },
  props: ['domain'],
  data () {
    return {
      showConfigHelp: false,
      showDetail: false
    }
  }
}
</script>
