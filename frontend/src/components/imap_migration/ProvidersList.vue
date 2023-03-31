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
    :items="providers"
    :search="search"
    item-key="name"
    single-expand
    :expanded.sync="expanded"
    class="elevation-1"
    show-select
    @click:row="(item, slot) => slot.expand(!slot.isExpanded)"
    >
    <template v-slot:item.secured="{ item }">
      <v-icon
        v-if="item.secured === true"
        color="green"
        >
        mdi-lock
      </v-icon>
      <v-icon
        color="red"
        v-else
        >
        mdi-lock-off
      </v-icon>
    </template>
    <template v-slot:item.domains="{ item }">
      <v-chip
        v-if="item.domains.length > 0"
        >
        {{item.domains.length}} associated domain(s)
      </v-chip>
      <v-chip
        v-else
        >
        No associated domain
      </v-chip>
    </template>
    <template v-slot:expanded-item="{ headers, item }">
      <td :colspan="headers.length">
        <v-chip
          v-for="(domain, index) in item.domains"
          :key="index"
          >
          <template v-if="domain.new_domain">
          {{domain.name}} --> {{domain.new_domain.name}}
          </template>
          <template v-else>
          {{domain.name}} --> {{domain.name}}
          </template>
        </v-chip>
      </td>
    </template>
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

import { mapGetters } from 'vuex'
import { bus } from '@/main'
import MenuItems from '@/components/tools/MenuItems'

export default {
  components: {
    MenuItems
  },
  computed: mapGetters({
    providers: 'providers/providers'
  }),
  data () {
    return {
      headers: [
        { text: this.$gettext('Name'), value: 'name' },
        { text: this.$gettext('Address'), value: 'address' },
        { text: this.$gettext('Port'), value: 'port' },
        { text: this.$gettext('Secured'), value: 'secured' },
        { text: this.$gettext('Associated domains'), value: 'domains' },
        { text: this.$gettext('Actions'), value: 'actions', sortable: false, align: 'right' }
      ],
      selected: [],
      search: '',
      expanded: []
    }
  },
  methods: {
    deleteProvider (provider) {
      this.$store.dispatch('providers/deleteProvider', { id: provider.id }).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Provider deleted') })
      })
    },
    editProvider (provider) {
      this.$router.push({ name: 'ProviderEdit', params: { id: provider.id } })
    },
    loadAssociatedDomains ({ item, value }) {
      if (!value) {
        return
      }
      this.$set(this.item.domains)
    },
    getMenuItems (item) {
      const result = []
      result.push({
        label: this.$gettext('Delete'),
        icon: 'mdi-delete-outline',
        onClick: this.deleteProvider,
        color: 'red'
      })
      result.push({
        label: this.$gettext('Edit'),
        icon: 'mdi-circle-edit-outline',
        onClick: this.editProvider
      })
      return result
    }
  },
  created () {
    this.$store.dispatch('providers/getProviders')
  }
}
</script>
