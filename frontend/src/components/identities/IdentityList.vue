<template>
<v-card class="mt-6">
  <v-toolbar flat>
    <v-menu offset-y>
      <template v-slot:activator="{ on, attrs }">
        <v-btn v-bind="attrs" v-on="on" small>
          <translate>Actions</translate> <v-icon right>mdi-chevron-down</v-icon>
        </v-btn>
      </template>
      <v-list dense>
        <menu-items :items="getActionMenuItems()"/>
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
      />
  </v-toolbar>

  <v-data-table
    v-model="selected"
    :headers="headers"
    :items="identities"
    :search="search"
    :loading="loading"
    item-key="identity"
    class="elevation-1"
    show-select
    >
    <template v-slot:item.identity="{ item }">
      <template v-if="item.type === 'account'">
        <router-link :to="{ name: 'AccountDetail', params: { id: item.pk } }">
          {{ item.identity }}
        </router-link>
      </template>
      <template v-else>
        <router-link :to="{ name: 'AliasDetail', params: { id: item.pk } }">
          {{ item.identity }}
        </router-link>
      </template>
    </template>
    <template v-slot:item.tags="{ item }">
      <v-chip v-for="(tag, index) in item.tags"
              :key="tag.name"
              :color="(tag.type !== 'idt') ? 'primary' : 'default'"
              :class="(index > 0) ? 'ml-2' : ''"
              small
              >
        {{ tag.label }}
      </v-chip>
    </template>
    <template v-slot:item.actions="{ item }">
      <template v-if="item.possible_actions.length !== 0">
        <v-icon size="2.5em" color="blue">mdi-circle-small</v-icon>
      </template>
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn icon v-bind="attrs" v-on="on">
            <v-icon>mdi-dots-horizontal</v-icon>
          </v-btn>
        </template>
        <menu-items :items="getMenuItems(item)" :object="item" />
      </v-menu>
    </template>
  </v-data-table>
  <confirm-dialog ref="confirmAlias" />
  <confirm-dialog ref="confirmAccount">
    <v-checkbox v-model="keepAccountFolder"
                :label="'Do not delete account folder'|translate"
                hide-details
                />
  </confirm-dialog>
</v-card>
</template>

<script>
import { bus } from '@/main'
import identities from '@/api/identities'
import accounts from '@/api/accounts'
import aliases from '@/api/aliases'
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import MenuItems from '@/components/tools/MenuItems'
import repository from '@/api/repository'

export default {
  components: {
    ConfirmDialog,
    MenuItems
  },
  data () {
    return {
      headers: [
        { text: this.$gettext('Name'), value: 'identity' },
        { text: this.$gettext('Fullname/recipient'), value: 'name_or_rcpt' },
        { text: this.$gettext('Tags'), value: 'tags' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      identities: [],
      keepAccountFolder: false,
      loading: true,
      search: '',
      selected: []
    }
  },
  methods: {
    sleep (milliseconds) {
      return new Promise((resolve) => setTimeout(resolve, milliseconds))
    },
    async deleteAlias (alias, confirmDialog = true) {
      if (confirmDialog) {
        const confirm = await this.$refs.confirmAlias.open(
          this.$gettext('Warning'),
          this.$gettext(
            'Do you really want to delete the alias %{ alias }?',
            { alias: alias.identity }
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
      }
      aliases.delete(alias.pk).then(() => {
        if (confirmDialog) {
          this.fetchIdentities()
          bus.$emit('notification', { msg: this.$gettext('Alias deleted') })
        }
      })
    },
    async deleteAccount (account, confirmDialog = true) {
      if (confirmDialog) {
        const confirm = await this.$refs.confirmAccount.open(
          this.$gettext('Warning'),
          this.$gettextInterpolate(
            'Do you really want to delete the account %{ account }?',
            { account: account.identity }
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
      }
      const data = { keepdir: this.keepAccountFolder }
      accounts.delete(account.pk, data).then(() => {
        this.keepAccountFolder = false
        if (confirmDialog) {
          bus.$emit('notification', { msg: this.$gettext('Account deleted') })
          this.fetchIdentities()
        }
      }).catch(error => {
        bus.$emit('notification', { msg: error.response.data, type: 'error' })
      })
    },
    async deleteIdentities () {
      if (this.selected.length === 0) {
        return
      }
      const confirm = await this.$refs.confirmAlias.open(
        this.$gettext('Warning'),
        this.$gettext(
          'Do you really want to delete the selected identities?'
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
      for (const item of this.selected) {
        if (item.type === 'account') {
          this.deleteAccount(item, false)
        } else if (item.type === 'alias') {
          this.deleteAlias(item, false)
        }
        await this.sleep(100)
      }
      bus.$emit('notification', { msg: this.$gettext('Identities deleted') })
      this.fetchIdentities()
    },
    editAccount (account) {
      this.$router.push({ name: 'AccountEdit', params: { id: account.pk } })
    },
    editAlias (alias) {
      this.$router.push({ name: 'AliasEdit', params: { id: alias.pk } })
    },
    fetchIdentities () {
      identities.getAll().then(resp => {
        this.identities = resp.data
        this.selected = []
        this.loading = false
      })
    },
    downloadFile (options) {
      repository.get(options.url).then(resp => {
        const url = window.URL.createObjectURL(
          new Blob([resp.data], { type: options.content_type }))
        const link = document.createElement('a')
        link.style.display = 'none'
        link.href = url
        link.download = options.filename
        document.body.appendChild(link)
        link.click()
        window.URL.revokeObjectURL(link.href)
        document.body.removeChild(link)
      })
    },
    getMenuItems (item) {
      const result = []
      if (item.type === 'account') {
        item.possible_actions.forEach(element => {
          result.push({
            label: element.label,
            icon: element.icon,
            onClick: () => {
              if (element.type === 'download') {
                this.downloadFile(element)
              }
              this.fetchIdentities()
            }
          })
        })
        result.push({
          label: this.$gettext('Edit'),
          icon: 'mdi-circle-edit-outline',
          onClick: this.editAccount
        })
        result.push({
          label: this.$gettext('Delete'),
          icon: 'mdi-delete-outline',
          onClick: this.deleteAccount,
          color: 'red'
        })
      } else if (item.type === 'alias') {
        result.push({
          label: this.$gettext('Edit'),
          icon: 'mdi-circle-edit-outline',
          onClick: this.editAlias
        })
        result.push({
          label: this.$gettext('Delete'),
          icon: 'mdi-delete-outline',
          onClick: this.deleteAlias,
          color: 'red'
        })
      }
      return result
    },
    getActionMenuItems () {
      const result = []
      if (this.selected.length > 0) {
        result.push({ label: this.$gettext('Delete'), icon: 'mdi-delete-outline', onClick: this.deleteIdentities, color: 'red' })
      }
      result.push({ label: 'Reload', icon: 'mdi-reload', onClick: this.fetchIdentities })
      return result
    }
  },
  mounted () {
    this.fetchIdentities()
  }
}
</script>
