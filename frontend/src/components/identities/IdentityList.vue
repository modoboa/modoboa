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
      />
  </v-toolbar>

  <v-data-table
    v-model="selected"
    :headers="headers"
    :items="identities"
    :search="search"
    item-key="identity"
    class="elevation-1"
    show-select
    >
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
      <div class="text-right">
        <v-menu offset-y>
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-horizontal</v-icon>
            </v-btn>
          </template>
          <menu-items :items="getMenuItems(item)" :object="item" />
        </v-menu>
      </div>
    </template>
  </v-data-table>

</v-card>
</template>

<script>
import identities from '@/api/identities'
import MenuItems from '@/components/tools/MenuItems'

export default {
  components: {
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
      search: '',
      selected: []
    }
  },
  methods: {
    editAccount (account) {
      this.$router.push({ name: 'AccountEdit', params: { id: account.pk } })
    },
    fetchIdentities () {
      identities.getAll().then(resp => {
        this.identities = resp.data
      })
    },
    getMenuItems (item) {
      return [
        { label: this.$gettext('Edit'), icon: 'mdi-circle-edit-outline', onClick: this.editAccount }
      ]
    }
  },
  mounted () {
    this.fetchIdentities()
  }
}
</script>
