<template>
<v-card class="mt-6">
  <v-toolbar flat>
    <v-spacer></v-spacer>
    <v-text-field
      v-model="search"
      prepend-inner-icon="mdi-magnify"
      :placeholder="'Search'|translate"
      filled
      outlined
      dense
      hide-details
      />
  </v-toolbar>
  <v-data-table
    :headers="headers"
    :items="messages"
    :search="search"
    class="elevation-1"
    :options.sync="options"
    :server-items-length="total"
    >
    <template v-slot:item.date="{ item }">
      {{ item.date|date }}
    </template>
    <template v-slot:item.sender="{ item }">
      {{ item.sender|truncate(50) }}
    </template>
  </v-data-table>
</v-card>
</template>

<script>
import logs from '@/api/logs'

export default {
  data () {
    return {
      messages: [],
      headers: [
        { text: this.$gettext('Queue ID'), value: 'queue_id' },
        { text: this.$gettext('Date'), value: 'date', width: '20%' },
        { text: this.$gettext('Status'), value: 'status' },
        { text: this.$gettext('To'), value: 'rcpt' },
        { text: this.$gettext('From'), value: 'sender' }
      ],
      loading: true,
      options: {},
      search: '',
      total: 0
    }
  },
  methods: {
    fetchMessages () {
      let order
      if (this.options.sortBy.length) {
        order = (this.options.sortDesc[0] ? '-' : '') + this.options.sortBy[0]
      }
      const params = {
        ordering: order,
        page: this.options.page,
        page_size: this.options.itemsPerPage,
        search: this.search
      }
      this.loading = true
      logs.getMessages(params).then(response => {
        this.messages = response.data.results
        this.total = response.data.count
        this.loading = false
      })
    }
  },
  watch: {
    options: {
      handler () {
        this.fetchMessages()
      },
      deep: true
    },
    search (val) {
      this.fetchMessages()
    }
  }
}
</script>
