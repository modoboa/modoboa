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
  <v-data-table
    v-model="selected"
    :headers="headers"
    :items="migrations"
    :search="search"
    item-key="pk"
    :options.sync="options"
    :server-items-length="totalMigrations"
    :loading="loading"
    class="elevation-1"
    show-select
    >
    <template v-slot:item.actions="{ item }">
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
</v-card>
</template>

<script>
import Migration from '@/api/imap_migration/migrations'
import MenuItems from '@/components/tools/MenuItems'
import { bus } from '@/main'

export default {
  components: {
    MenuItems
  },
  data () {
    return {
      migrations: [],
      headers: [
        { text: this.$gettext('Provider'), value: 'provider' },
        { text: this.$gettext('Old account'), value: 'old_account' },
        { text: this.$gettext('New account'), value: 'new_account' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }

      ],
      selected: [],
      loading: true,
      search: '',
      options: {},
      totalMigrations: 0
    }
  },
  methods: {
    deleteMigration (migration) {
      this.$dialog.confirm(
        this.$gettext('Remove this migration?'), {
          cancelText: this.$gettext('Cancel'),
          okText: this.$gettext('Proceed')
        }
      ).then(dialog => {
        Migration.deleteMigration(migration.id).then(response => {
          bus.$emit('notification', { msg: this.$gettext('Provider deleted') })
          this.migrations = this.migrations.filter(item => {
            return item.id !== migration.id
          })
        })
      })
    },
    getMigrations (filter) {
      this.loading = true
      let query = {}
      if (filter !== undefined) {
        query = { params: { search: filter } }
      }
      Migration.getMigrations(query).then(response => {
        this.migrations = response.data
        this.loading = false
      })
    },
    getMenuItems (item) {
      const result = []
      result.push({
        label: this.$gettext('Delete'),
        icon: 'mdi-delete-outline',
        onClick: this.deleteMigration,
        color: 'red'
      })
      return result
    }
  },
  mounted () {
    this.getMigrations()
  }
}
</script>
