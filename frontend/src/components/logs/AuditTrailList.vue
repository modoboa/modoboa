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
    :items="logs"
    :search="search"
    class="elevation-1"
    :options.sync="options"
    :server-items-length="total"
    >
    <template v-slot:item.level="{ item }">
      <v-chip :color="getLevelColor(item.level)" text-color="white" small>
        {{ item.level }}
      </v-chip>
    </template>
  </v-data-table>
</v-card>
</template>

<script>
import logs from '@/api/logs'
import debounce from 'debounce'
export default {
  data () {
    return {
      logs: [],
      headers: [
        { text: this.$gettext('Date'), value: 'date_created' },
        { text: this.$gettext('Level'), value: 'level' },
        { text: this.$gettext('Logger'), value: 'logger' },
        { text: this.$gettext('Message'), value: 'message' }
      ],
      loading: true,
      options: {},
      search: '',
      total: 0
    }
  },
  methods: {
    getLevelColor (level) {
      if (level === 'INFO') {
        return 'primary'
      }
      if (level === 'WARNING') {
        return 'orange'
      }
      if (level === 'CRITICAL' || level === 'ERROR') {
        return 'red'
      }
      return ''
    },
    fetchLogs () {
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
      logs.getAuditTrail(params).then(response => {
        this.logs = response.data.results
        this.total = response.data.count
        this.loading = false
      })
    }
  },
  created () {
    this.fetchLogs = debounce(this.fetchLogs, 500)
  },
  watch: {
    options: {
      handler () {
        this.fetchLogs()
      },
      deep: true
    },
    search (val) {
      this.fetchLogs()
    }
  }
}
</script>
