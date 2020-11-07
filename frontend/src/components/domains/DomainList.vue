<template>
  <div>
    <v-toolbar flat color="white">
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
        ></v-text-field>
      <v-spacer></v-spacer>
      <v-btn class="mr-2" fab small>
        <v-icon>mdi-file-import-outline</v-icon>
      </v-btn>
      <v-btn class="mr-2" fab small>
        <v-icon>mdi-file-export-outline</v-icon>
      </v-btn>
      <v-btn fab small color="secondary" :to="{ name: 'DomainAdd' }">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
    </v-toolbar>
    <v-data-table :headers="headers" :items="domains" :search="search" class="elevation-1">
      <template v-slot:item.name="{ item }">
        <router-link :to="{ name: 'DomainDetail', params: { pk: item.pk } }">
          {{ item.name }}
        </router-link>
      </template>
      <template v-slot:item.tags="{ }">
        <v-chip label x-small><translate>Domain</translate></v-chip>
      </template>
      <template v-slot:item.dns_status="{ item }">
        <v-chip v-if="item.dns_status.checks === 'disabled'"
                label x-small><translate>Disabled</translate></v-chip>
        <v-chip v-if="item.dns_status.checks === 'pending'"
                color="secondary" label x-small><translate>Pending</translate></v-chip>
        <span v-if="item.dns_status.checks === 'active'">
          <v-chip v-if="item.dns_status.mx"
                  :color="getDNSTagType(item.dns_status.mx)"
                  class="mr-1"
                  label
                  x-small
                  >
            MX
          </v-chip>
          <v-chip v-if="item.dns_status.dnsbl"
                  :color="getDNSTagType(item.dns_status.dnsbl)"
                  label
                  x-small
                  >
            DNSBL
          </v-chip>
        </span>
      </template>
      <template v-slot:item.allocated_quota_in_percent="{ item }">
        <v-progress-linear v-model="item.allocated_quota_in_percent" />
      </template>
      <template v-slot:item.actions="{ item }">
        <div class="text-right">
          <v-btn icon x-small :to="{ name: 'DomainEdit', params: { domainPk: item.pk }}">
            <v-icon>mdi-circle-edit-outline</v-icon>
          </v-btn>
          <v-btn
            icon
            x-small
            :title="'Delete this domain' | translate"
            @click="confirmDelete(item)">
            <v-icon>mdi-delete-outline</v-icon>
          </v-btn>
        </div>
      </template>
    </v-data-table>

  <confirm-dialog v-model="showConfirmDialog"
                  :message="deleteDomainMsg"
                  @confirm="deleteDomain" />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  components: {
    ConfirmDialog
  },
  computed: mapGetters({
    domains: 'domains/domains'
  }),
  data () {
    return {
      headers: [
        { text: 'Name', value: 'name' },
        { text: 'Tags', value: 'tags' },
        { text: 'DNS status', value: 'dns_status', sortable: false },
        { text: 'Quota', value: 'allocated_quota_in_percent' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false }
      ],
      deleteDomainMsg: this.$gettext('Confirm deletion?'),
      selectedDomain: null,
      showConfirmDialog: false,
      search: ''
    }
  },
  created () {
    this.$store.dispatch('domains/getDomains')
  },
  methods: {
    confirmDelete (domain) {
      this.selectedDomain = domain
      this.showConfirmDialog = true
    },
    deleteDomain () {

    },
    getDNSTagType (value) {
      if (value === 'unknown') {
        return 'orange'
      }
      if (value === 'ok') {
        return 'warning'
      }
      return 'success'
    }
  }
}
</script>
