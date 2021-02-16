<template>
<v-card>
  <v-card-title>
    <translate class="headline">DNS configuration overview for {{ domain.name }}</translate>
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
          <translate>autoconfig record (Mozilla): {{ detail.autoconfig_record.value }}</translate>
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
          <translate>autodiscover record (Microsoft): {{ detail.autodiscover_record.value }}</translate>
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
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      color="grey darken-1"
      text
      @click="close"
      >
      <translate>Close</translate>
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import domains from '@/api/domains'

export default {
  props: ['domain'],
  data () {
    return {
      detail: {},
      mxRecordHeaders: [
        { text: this.$gettext('Name'), value: 'name' },
        { text: this.$gettext('Address'), value: 'address' },
        { text: this.$gettext('Updated'), value: 'updated' }
      ]
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.detail = {}
    }
  },
  watch: {
    domain: {
      handler: function (val) {
        domains.getDomainDNSDetail(val.pk).then(resp => {
          this.detail = resp.data
        })
      },
      immediate: true
    }
  }
}
</script>
