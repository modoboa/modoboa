<template>
<v-card v-if="value">
  <v-card-title>
    <span class="headline">DNS</span>
    <v-btn icon :title="'DNS configuration help'|translate" @click="showConfigHelp = true">
      <v-icon>mdi-information-outline</v-icon>
    </v-btn>
  </v-card-title>
  <v-card-text>
    <translate class="overline">MX records</translate>
    <v-data-table
      :headers="mxRecordHeaders"
      :items="detail.mx_records"
      hide-default-footer
      >
      <template v-slot:item.updated="{ item }">
        {{ item.updated|date }}
      </template>
    </v-data-table>
    <translate class="overline">Auto configuration</translate>
    <v-row>
      <v-col>
        <v-chip
          v-if="detail.autoconfig_record"
          color="success"
          >
          <translate
            :translate-params="{ value: detail.autoconfig_record.value }"
            >
            autoconfig record (Mozilla): %{ value }
          </translate>
        </v-chip>
        <v-chip
          v-else
          color="warning"
          >
          <translate>autoconfig record (Mozilla) not found</translate>
        </v-chip>
      </v-col>
      <v-col>
        <v-chip
          v-if="detail.autodiscover_record"
          color="success"
          >
          <translate
            :translate-params="{ value: detail.autodiscover_record.value }"
            >
            autodiscover record (Microsoft): %{ value }
          </translate>
        </v-chip>
        <v-chip
          v-else
          color="warning"
          >
          <translate>autodiscover record (Microsoft) not found</translate>
        </v-chip>
      </v-col>
    </v-row>
    <translate class="overline">Authentication</translate>
    <v-row>
      <v-col>
        <v-chip
          v-if="detail.spf_record"
          color="success"
          >
          <translate>SPF record found</translate>
        </v-chip>
        <v-chip
          v-else
          color="error"
          >
          <translate>SPF record not found</translate>
        </v-chip>
      </v-col>
      <v-col>
        <v-chip
          v-if="detail.dkim_record"
          color="success"
          >
          <translate>DKIM record found</translate>
        </v-chip>
        <v-chip
          v-else
          color="error"
          >
          <translate>DKIM record not found</translate>
        </v-chip>
      </v-col>
      <v-col>
        <v-chip
          v-if="detail.dmarc_record"
          color="success"
          >
          <translate>DMARC record found</translate>
        </v-chip>
        <v-chip
          v-else
          color="error"
          >
          <translate>DMARC record not found</translate>
        </v-chip>
      </v-col>
    </v-row>
    <v-row v-if="value.enable_dkim">
      <v-col cols="3"><translate>DKIM key</translate></v-col>
      <v-col cols="9">
        <div v-if="value.dkim_private_key_path && value.dkim_public_key">
          <v-btn color="primary" small @click="showDKIMKey = true">
            <translate>Show key</translate>
          </v-btn>
          <v-btn icon :title="'Generate a new DKIM key'|translate" @click="generateNewKey">
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </div>
        <translate v-else>Not generated</translate>
      </v-col>
    </v-row>
  </v-card-text>
  <v-dialog v-model="showConfigHelp"
            max-width="800px"
            persistent
            >
    <domain-dns-config :domain="value" @close="showConfigHelp = false" />
  </v-dialog>
  <v-dialog v-model="showDKIMKey"
            max-width="800px"
            persistent
            >
    <domain-dkim-key :domain="value" @close="showDKIMKey = false" />
  </v-dialog>
</v-card>
</template>

<script>
import { bus } from '@/main'
import domains from '@/api/domains'
import DomainDKIMKey from './DomainDKIMKey'
import DomainDNSConfig from './DomainDNSConfig'

export default {
  props: ['value'],
  components: {
    'domain-dkim-key': DomainDKIMKey,
    'domain-dns-config': DomainDNSConfig
  },
  data () {
    return {
      detail: {},
      mxRecordHeaders: [
        { text: this.$gettext('Name'), value: 'name' },
        { text: this.$gettext('Address'), value: 'address' },
        { text: this.$gettext('Updated'), value: 'updated' }
      ],
      showConfigHelp: false,
      showDKIMKey: false
    }
  },
  methods: {
    generateNewKey () {
      const payload = {
        dkim_private_key_path: ''
      }
      domains.patchDomain(this.value.pk, payload).then(resp => {
        bus.$emit('notification', {
          msg: this.$gettext('A new key will be generated soon. Refresh the page in a moment to see it.'),
          type: 'success'
        })
        const domain = { ...this.value }
        domain.dkim_private_key_path = ''
        this.$emit('input', domain)
      })
    }
  },
  watch: {
    value: {
      handler: function (val) {
        if (val) {
          domains.getDomainDNSDetail(val.pk).then(resp => {
            this.detail = resp.data
          })
        }
      },
      immediate: true
    }
  }
}
</script>
