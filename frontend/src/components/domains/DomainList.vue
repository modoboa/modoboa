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
                  @click="openDNSDetail(item)"
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
              <menu-items :items="domainMenuItems" :object="item" />
            </v-menu>
          </div>
        </td>
      </tr>
    </template>
    <template v-slot:expanded-item="{ headers, item }">
      <tr class="grey lighten-4">
        <td :colspan="headers.length">
          <span v-for="alias in aliases[item.name]"
               :key="alias.name"
               class="mr-4"
               >
            <a href="#" class="mr-2" @click="editDomainAlias(item, alias)">{{ alias.name }}</a>
            <v-chip x-small color="success">DNS OK</v-chip>
          </span>
        </td>
      </tr>
    </template>
  </v-data-table>
  <confirm-dialog ref="confirm" />
  <v-dialog v-model="showDNSdetail"
            persistent
            max-width="800px">
    <dns-detail @close="showDNSdetail = false" :domain="selectedDomain" />
  </v-dialog>
  <v-dialog v-model="showDomainForm"
            persistent
            max-width="800px"
            >
    <domain-form :domain="selectedDomain" @close="showDomainForm = false" />
  </v-dialog>
  <v-dialog v-model="showAliasForm"
            persistent
            max-width="800px">
    <domain-alias-form
      @close="closeDomainAliasForm"
      :domain-alias="selectedDomainAlias"
      @alias-deleted="domainAliasDeleted"
      />
  </v-dialog>
  <v-dialog v-model="showAdminList"
            persistent
            max-width="800px"
            >
    <administrator-list
      :domain="selectedDomain"
      @close="showAdminList = false"
      />
  </v-dialog>
</v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import domainApi from '@/api/domains'
import AdministratorList from './AdministratorList'
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import DNSDetail from '@/components/domains/DNSDetail'
import DomainAliasForm from '@/components/domains/DomainAliasForm'
import DomainForm from '@/components/domains/DomainForm'
import MenuItems from '@/components/tools/MenuItems'

export default {
  components: {
    AdministratorList,
    ConfirmDialog,
    'dns-detail': DNSDetail,
    DomainAliasForm,
    DomainForm,
    MenuItems
  },
  computed: mapGetters({
    domains: 'domains/domains'
  }),
  data () {
    return {
      domainMenuItems: [
        { label: this.$gettext('Administrators'), icon: 'mdi-account-supervisor', onClick: this.openAdminList },
        { label: this.$gettext('Edit'), icon: 'mdi-circle-edit-outline', onClick: this.editDomain },
        { label: this.$gettext('Delete'), icon: 'mdi-delete-outline', onClick: this.deleteDomain, color: 'red' }
      ],
      headers: [
        { text: 'Name', value: 'name' },
        { text: 'Aliases', value: 'domainalias_count' },
        { text: 'DNS status', value: 'dns_global_status', sortable: false, align: 'center' },
        { text: 'Sending limit', value: 'message_limit' },
        { text: 'Quota', value: 'allocated_quota_in_percent' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      selectedDomain: null,
      selectedDomainAlias: null,
      showAdminList: false,
      showConfirmDialog: false,
      showAliasForm: false,
      showDNSdetail: false,
      showDomainForm: false,
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
    closeDomainAliasForm () {
      this.showAliasForm = false
      this.selectedDomain = null
      this.selectedDomainAlias = null
    },
    async deleteDomain (domain) {
      const confirm = await this.$refs.confirm.open(
        this.$gettext('Warning'),
        this.$gettext(`Do you really want to delete the domain ${domain.name}?`),
        {
          color: 'error',
          cancelLabel: this.$gettext('No'),
          agreeLabel: this.$gettext('Yes')
        }
      )
      if (!confirm) {
        return
      }
      this.$store.dispatch('domains/deleteDomain', { id: domain.pk }).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Domain delete') })
      })
    },
    domainAliasDeleted () {
      const newList = this.aliases[this.selectedDomain.name].filter(alias => {
        return alias.pk !== this.selectedDomainAlias.pk
      })
      this.$set(this.aliases, this.selectedDomain.name, newList)
      this.closeDomainAliasForm()
    },
    editDomain (domain) {
      this.selectedDomain = domain
      this.showDomainForm = true
    },
    editDomainAlias (domain, alias) {
      this.selectedDomain = domain
      this.selectedDomainAlias = alias
      this.showAliasForm = true
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
    openDNSDetail (domain) {
      this.selectedDomain = domain
      this.showDNSdetail = true
    },
    openAdminList (domain) {
      this.selectedDomain = domain
      this.showAdminList = true
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
