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
          <router-link :to="{ name: 'DomainDetail', params: { id: item.pk } }">
            {{ item.name }}
          </router-link>
          <v-chip
            v-if="item.type === 'relaydomain'"
            small
            color="primary"
            class="ml-2"
            >
            <translate>Relay</translate>
          </v-chip>
          <translate v-if="!item.enabled" class="ml-2 grey--text">(disabled)</translate>
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
          <dns-status-chip :status="item.dns_global_status" />
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
                <v-badge
                  v-if="item.opened_alarms_count"
                  bordered
                  color="error"
                  icon="mdi-bell"
                  overlap
                  >
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-dots-horizontal</v-icon>
                  </v-btn>
                </v-badge>
                <v-btn v-else icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-dots-horizontal</v-icon>
                </v-btn>
              </template>
              <menu-items :items="getDomainMenuItems(item)" :object="item" />
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
  <confirm-dialog ref="confirm">
    <v-checkbox v-model="keepDomainFolder"
                :label="'Do not delete domain folder'|translate"
                hide-details
                />
  </confirm-dialog>
  <v-dialog v-model="showAliasForm"
            persistent
            max-width="800px">
    <domain-alias-form
      @close="closeDomainAliasForm"
      :domain-alias="selectedDomainAlias"
      @alias-created="domainAliasCreated"
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
      dialog-mode
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
import DNSStatusChip from './DNSStatusChip'
import DomainAliasForm from '@/components/domains/DomainAliasForm'
import MenuItems from '@/components/tools/MenuItems'

export default {
  components: {
    AdministratorList,
    ConfirmDialog,
    'dns-status-chip': DNSStatusChip,
    DomainAliasForm,
    MenuItems
  },
  computed: mapGetters({
    domains: 'domains/domains'
  }),
  data () {
    return {
      headers: [
        { text: this.$gettext('Name'), value: 'name' },
        { text: this.$gettext('Aliases'), value: 'domainalias_count' },
        { text: this.$gettext('DNS status'), value: 'dns_global_status', sortable: false, align: 'center' },
        { text: this.$gettext('Sending limit'), value: 'message_limit' },
        { text: this.$gettext('Quota'), value: 'allocated_quota_in_percent' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      keepDomainFolder: false,
      selectedDomain: null,
      selectedDomainAlias: null,
      showAdminList: false,
      showConfirmDialog: false,
      showAliasForm: false,
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
        this.$gettextInterpolate(
          'Do you really want to delete the domain %{ domain }?',
          { domain: domain.name }
        ),
        {
          color: 'error',
          cancelLabel: this.$gettext('No'),
          agreeLabel: this.$gettext('Yes')
        }
      )
      if (!confirm) {
        return
      }
      const data = { keep_folder: this.keepDomainFolder }
      this.$store.dispatch('domains/deleteDomain', { id: domain.pk, data }).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Domain deleted') })
        this.keepDomainFolder = false
      })
    },
    domainAliasCreated (domainAlias) {
      this.$store.dispatch('domains/getDomains')
    },
    domainAliasDeleted () {
      const newList = this.aliases[this.selectedDomain.name].filter(alias => {
        return alias.pk !== this.selectedDomainAlias.pk
      })
      this.$set(this.aliases, this.selectedDomain.name, newList)
      if (!newList.length) {
        this.expanded = []
      }
      this.$store.dispatch('domains/getDomains')
      this.closeDomainAliasForm()
    },
    editDomain (domain) {
      this.$router.push({ name: 'DomainEdit', params: { id: domain.pk } })
    },
    editDomainAlias (domain, alias) {
      this.selectedDomain = domain
      this.selectedDomainAlias = alias
      this.showAliasForm = true
    },
    loadAliases ({ item, value }) {
      if (!value) {
        return
      }
      domainApi.getDomainAliases(item.name).then(resp => {
        this.$set(this.aliases, item.name, resp.data)
      })
    },
    openAdminList (domain) {
      this.selectedDomain = domain
      this.showAdminList = true
    },
    showAliases (item) {
      this.expanded = [{ item }]
    },
    getDomainMenuItems (domain) {
      const result = [
        { label: this.$gettext('Administrators'), icon: 'mdi-account-supervisor', onClick: this.openAdminList },
        { label: this.$gettext('Edit'), icon: 'mdi-circle-edit-outline', onClick: this.editDomain },
        { label: this.$gettext('Delete'), icon: 'mdi-delete-outline', onClick: this.deleteDomain, color: 'red' }
      ]
      if (domain.opened_alarms_count) {
        result.push({
          label: this.$gettext('Alarms'),
          icon: 'mdi-bell',
          color: 'red',
          onClick: () => this.$router.push({ name: 'Alarms' })
        })
      }
      return result
    }
  }
}
</script>

<style scoped>
.v-text-field--outlined >>> fieldset {
  border-color: #BFC5D2;
}
.v-input--checkbox >>> .v-label {
  font-size: 0.875rem !important;
}
</style>
