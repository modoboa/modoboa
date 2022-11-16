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
    :options.sync="options"
    :server-items-length="totalAlarms"
    :loading="loading"
    class="elevation-1"
    show-select
    >
    <template v-slot:item.status="{ item }">
      <v-chip
        v-if="item.status === 1"
        color="warning"
        small
        >
        <translate>Opened</translate>
      </v-chip>
      <v-chip
        v-else
        color="info"
        small
        >
        <translate>Closed</translate>
      </v-chip>
    </template>
    <template v-slot:item.mailbox="{ item }">
      <template v-if="item.mailbox">
        {{ item.mailbox.address }}@{{ item.domain.name }}
      </template>
    </template>
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
        { text: this.$gettext('Triggered'), value: 'created' },
        { text: this.$gettext('Status'), value: 'status' },
        { text: this.$gettext('Domain'), value: 'domain.name', sortable: false },
        { text: this.$gettext('Mailbox'), value: 'mailbox', sortable: false },
        { text: this.$gettext('Message'), value: 'title' }
      ],
      loading: true,
      options: {},
      search: '',
      selected: [],
      totalAlarms: 0
    }
  },
  methods: {
    fetchAlarms () {
      const params = {
        page: this.options.page
      }
      if (this.options.sortBy) {
        params.ordering = this.options.sortBy.map(item => this.options.sortDesc[0] ? `-${item}` : item).join(',')
      }
      if (this.search !== '') {
        params.search = this.search
      }
      this.loading = true
      alarms.getAll(params).then(resp => {
        this.alarms = resp.data.results
        this.totalAlarms = resp.data.count
        this.loading = false
      })
    }
  },
  mounted () {
    this.fetchAlarms()
  },
  watch: {
    options: {
      handler () {
        this.fetchAlarms()
      },
      deep: true
    },
    search () {
      this.fetchAlarms()
    }
  }
}
</script>
