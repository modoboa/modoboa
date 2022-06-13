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
    :items="alarms"
    :search="search"
    item-key="pk"
    class="elevation-1"
    show-select
    >
    <template v-slot:item.created="{ item }">
      {{ item.created|date }}
    </template>
  </v-data-table>
</v-card>
</template>

<script>
import alarms from '@/api/alarms'

export default {
  data () {
    return {
      alarms: [],
      headers: [
        { text: this.$gettext('Date'), value: 'created' },
        { text: this.$gettext('Domain'), value: 'domain.name' },
        { text: this.$gettext('Mailbox'), value: 'mailbox.name' },
        { text: this.$gettext('Message'), value: 'title' }
      ],
      search: '',
      selected: []
    }
  },
  mounted () {
    alarms.getAll().then(resp => {
      this.alarms = resp.data
    })
  }
}
</script>
