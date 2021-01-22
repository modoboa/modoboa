<template>
  <v-card class="mt-6">
    <v-toolbar flat>
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn v-bind="attrs" v-on="on" small>
            Actions <v-icon right>mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list dense>
        </v-list>
      </v-menu>
      <v-spacer></v-spacer>
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        placeholder="Search"
        filled
        outlined
        dense
        hide-details
        ></v-text-field>
    </v-toolbar>
    <v-data-table v-model="selected"
                  :headers="headers"
                  :items="domains"
                  :search="search"
                  item-key="name"
                  class="elevation-1"
                  show-select
                  single-expand
                  show-expand
                  :expanded.sync="expanded"
                  @item-expanded="loadAliases"
                  @click:row="showAliases"
                  >
      <template v-slot:item.select="{ }">
        <v-checkbox />
      </template>
      <template v-slot:item.name="{ item }">
        <router-link :to="{ name: 'DomainDetail', params: { pk: item.pk } }">
          {{ item.name }}
        </router-link>
      </template>
      <template v-slot:item.domainalias_count="{ item }">
        {{ item.domainalias_count }} aliases
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
      <template v-slot:item.message_limit="{ item }">
        <v-progress-linear v-model="item.allocated_quota_in_percent" />
      </template>
      <template v-slot:item.allocated_quota_in_percent="{ item }">
        <v-progress-linear v-model="item.allocated_quota_in_percent" />
      </template>
      <template v-slot:item.actions="{ item }">
        <div class="text-right">
          <v-menu offset-y>
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon v-bind="attrs" v-on="on">
                <v-icon>mdi-dots-horizontal</v-icon>
              </v-btn>
            </template>
            <v-list dense>
              <v-list-item :to="{ name: 'DomainEdit', params: { domainPk: item.pk }}">
                <v-list-item-icon>
                  <v-icon>mdi-circle-edit-outline</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title><translate>Edit</translate></v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <v-list-item @click="confirmDelete(item)" color="red">
                <v-list-item-icon>
                  <v-icon color="red">mdi-delete-outline</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title><translate>Delete</translate></v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </template>
      <template v-slot:expanded-item="{ headers, item }">
        <td :colspan="headers.length">
          <span class="mr-4" v-for="alias in aliases[item.name]" :key="alias.name">
            {{ alias.name }} <v-chip color="success" label x-small>DNS OK</v-chip>
          </span>
        </td>
      </template>
    </v-data-table>

  <confirm-dialog v-model="showConfirmDialog"
                  :message="deleteDomainMsg"
                  @confirm="deleteDomain" />
</v-card>
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
        { text: 'Aliases', value: 'domainalias_count' },
        { text: 'DNS status', value: 'dns_status', sortable: false },
        { text: 'Sending limit', value: 'message_limit' },
        { text: 'Quota', value: 'allocated_quota_in_percent' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      deleteDomainMsg: this.$gettext('Confirm deletion?'),
      selectedDomain: null,
      showConfirmDialog: false,
      search: '',
      selected: [],
      expanded: [],
      aliases: {}
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
    },
    loadAliases ({ item, value }) {
      if (!value) {
        return
      }
      this.$axios.get(`/domainaliases/?domain=${item.name}`).then(resp => {
        this.$set(this.aliases, item.name, resp.data)
      })
    },
    showAliases (item) {
      this.expanded = [{ item }]
    }
  }
}
</script>

<style scoped>
.v-text-field--outlined >>> fieldset {
  border-color: #BFC5D2;
}
</style>
