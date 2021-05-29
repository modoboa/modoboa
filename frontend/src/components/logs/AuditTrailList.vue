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
    :options.sync="pagination"
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

export default {
  data () {
    return {
      logs: [],
      headers: [
        { text: 'Date', value: 'date_created' },
        { text: 'Level', value: 'level' },
        { text: 'Logger', value: 'logger' },
        { text: 'Message', value: 'message' }
      ],
      loading: true,
      pagination: {
      },
      search: ''
    }
  },
  created () {
    logs.getAll().then(response => {
      this.logs = response.data
      this.loading = false
    })
  },
  methods: {
    getLevelColor (level) {
      if (level === 'INFO') {
        return 'primary'
      }
      if (level === 'WARNING') {
        return 'orange'
      }
      if (level === 'CRITICAL') {
        return 'red'
      }
      return ''
    }
  }
}
</script>
