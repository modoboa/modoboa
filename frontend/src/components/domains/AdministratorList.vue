<template>
<v-card>
  <v-card-title>
    <span class="headline">
      <translate v-if="dialogMode" class="headline">Administrators of {{ domain.name }}</translate>
      <translate v-else class="headline">Administrators</translate>
    </span>
  </v-card-title>
  <v-card-text>
    <v-data-table
      :headers="headers"
      :items="administrators"
      hide-default-footer
      >
      <template v-slot:item.username="{ item }">
        <span v-if="item.id">{{ item.username }}</span>
        <v-autocomplete
          v-else
          v-model="selectedAccount"
          :label="'Select an account'|translate"
          :items="accounts"
          item-text="username"
          return-object
          >
          <template v-slot:append-outer>
            <v-btn v-if="selectedAccount" icon color="primary" @click="addAdministrator">
              <v-icon>mdi-content-save</v-icon>
            </v-btn>
          </template>
        </v-autocomplete>
      </template>
      <template v-slot:item.name="{ item }">
        {{ item.first_name }} {{ item.last_name }}
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn v-if="item.id"
               icon
               color="red"
               @click="removeAdministrator(item)"
               :title="'Remove this administrator'|translate"
               >
          <v-icon>mdi-delete-outline</v-icon>
        </v-btn>
      </template>
    </v-data-table>
    <v-btn v-if="!hideAddBtn"
           small
           color="primary"
           outlined
           @click="addRow"
           >
      <v-icon small>mdi-plus</v-icon> <translate>Add administrator</translate>
    </v-btn>
  </v-card-text>
  <v-card-actions v-if="dialogMode">
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
import accounts from '@/api/accounts'
import domains from '@/api/domains'
import { bus } from '@/main'

export default {
  props: {
    domain: Object,
    dialogMode: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      accounts: [],
      administrators: [],
      headers: [
        { text: this.$gettext('Username'), value: 'username' },
        { text: this.$gettext('Name'), value: 'name' },
        { text: '', value: 'actions', align: 'right', sortable: false }
      ],
      hideAddBtn: false,
      selectedAccount: null
    }
  },
  methods: {
    addRow () {
      this.administrators.push({})
      this.hideAddBtn = true
    },
    close () {
      this.$emit('close')
      this.hideAddBtn = false
    },
    fetchAdministrators (domain) {
      domains.getDomainAdministrators(domain.pk).then(resp => {
        this.administrators = resp.data
      })
    },
    fetchAccounts () {
      accounts.getAll({ role: 'DomainAdmins' }).then(resp => {
        this.accounts = resp.data.filter(
          account => this.administrators.find(admin => admin.id === account.pk) === undefined
        )
      })
    },
    addAdministrator () {
      domains.addDomainAdministrator(this.domain.pk, this.selectedAccount.pk).then(resp => {
        this.fetchAdministrators(this.domain)
        this.accounts = this.accounts.filter(account => account.pk !== this.selectedAccount.pk)
        this.selectedAccount = null
        this.hideAddBtn = false
        bus.$emit('notification', { msg: this.$gettext('Administrator added') })
      })
    },
    removeAdministrator (admin) {
      domains.removeDomainAdministrator(this.domain.pk, admin.id).then(resp => {
        this.fetchAdministrators(this.domain)
        this.fetchAccounts()
        bus.$emit('notification', { msg: this.$gettext('Administrator removed') })
      })
    }
  },
  watch: {
    domain: {
      handler: function (value) {
        this.fetchAdministrators(value)
        this.fetchAccounts()
      },
      immediate: true
    }
  }
}
</script>
