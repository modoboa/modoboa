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
                  :expanded.sync="expanded"
                  @item-expanded="loadAliases"
                  @click:row="showAliases"
                  >
      <template v-slot:item="{ item, isExpanded, expand }">
        <tr>
          <td>
            <v-checkbox />
          </td>
          <td>
            <router-link :to="{ name: 'DomainDetail', params: { pk: item.pk } }">
              {{ item.name }}
            </router-link>
          </td>
          <td>
            {{ item.domainalias_count }} aliases
            <v-btn v-if="item.domainalias_count"
                   icon
                   @click="expand(!isExpanded)"
                   >
              <v-icon v-if="!isExpanded">mdi-chevron-down</v-icon>
              <v-icon v-else>mdi-chevron-up</v-icon>
            </v-btn>
          </td>
          <td>
            <v-chip :color="getDNSTagType(item.dns_global_status)"
                    small>
              {{ getDNSLabel(item.dns_global_status) }}
            </v-chip>
          </td>
          <td>
            <v-progress-linear v-model="item.allocated_quota_in_percent" />
          </td>
          <td>
            <v-progress-linear v-model="item.allocated_quota_in_percent" />
          </td>
          <td>
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
                  <v-list-item @click="deleteDomain(item)" color="red">
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
          </td>
        </tr>
      </template>
      <template v-slot:expanded-item="{ headers, item }">
        <tr>
          <td :colspan="headers.length">
            <v-chip v-for="alias in aliases[item.name]"
                    :key="alias.name"
                    class="mr-2"
                    pill
                    title="DNS OK"
                    >
              <v-icon left color="success">mdi-server-network</v-icon>
              {{ alias.name }}
              <v-btn class="ml-4" x-small icon><v-icon>mdi-circle-edit-outline</v-icon></v-btn>
              <v-btn x-small icon color="error"><v-icon>mdi-delete-outline</v-icon></v-btn>
            </v-chip>
          </td>
        </tr>
      </template>
    </v-data-table>
  <confirm-dialog ref="confirm" />
</v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import domainApi from '@/api/domains'
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
        { text: 'DNS status', value: 'dns_global_status', sortable: false, align: 'center' },
        { text: 'Sending limit', value: 'message_limit' },
        { text: 'Quota', value: 'allocated_quota_in_percent' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
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
    async deleteDomain (domain) {
      await this.$refs.confirm.open(
        this.$gettext('Warning'),
        this.$gettext(`Do you really want to delete the domain ${domain.name}?`),
        {
          color: 'error',
          cancelLabel: this.$gettext('No'),
          agreeLabel: this.$gettext('Yes')
        }
      )
    },
    getDNSLabel (value) {
      if (value === 'disabled') {
        return this.$gettext('Disabled')
      }
      if (value === 'pending') {
        return this.$gettext('Pending')
      }
      if (value === 'critical') {
        return this.$gettext('Problem')
      }
      if (value === 'ok') {
        return this.$gettext('Valid')
      }
      return this.$gettext('Unknown')
    },
    getDNSTagType (value) {
      if (value === 'disabled') {
        return ''
      }
      if (value === 'pending') {
        return 'info'
      }
      if (value === 'critical') {
        return 'error'
      }
      if (value === 'ok') {
        return 'success'
      }
      return 'warning'
    },
    loadAliases ({ item, value }) {
      if (!value) {
        return
      }
      domainApi.getDomainAliases(item.name).then(resp => {
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
