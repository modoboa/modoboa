<template>
  <v-layout>
    <v-flex>
      <v-toolbar flat color="white">
        <v-toolbar-title>Logs</v-toolbar-title>
        <v-divider class="mx-2" inset vertical></v-divider>
        <v-spacer></v-spacer>
        <v-text-field
            v-model="search"
            append-icon="search"
            label="Search"
            single-line
            hide-details
        ></v-text-field>
      </v-toolbar>
      <v-data-table :headers="headers"
                    :items="logs"
                    :search="search"
                    class="elevation-1"
                    v-bind:pagination.sync="pagination"
      >
        <template slot="items" slot-scope="props">
          <td>{{ props.item.date_created }}</td>
          <td>
            <v-chip v-if="props.item.level === 'INFO'"
                    color="primary" text-color="white" small>
              {{ props.item.level }}
            </v-chip>
            <v-chip v-if="props.item.level === 'WARNING'"
                    color="orange" text-color="white" small>
              {{ props.item.level }}
            </v-chip>
            <v-chip v-if="props.item.level === 'CRITICAL'"
                    color="red" text-color="white" small>
              {{ props.item.level }}
            </v-chip>
          </td>
          <td>{{ props.item.logger }}</td>
          <td>{{ props.item.message }}</td>
        </template>
      </v-data-table>
    </v-flex>
  </v-layout>
</template>

<script>
import * as api from '@/api'

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
                sortBy: 'date_created',
                descending: true,
                rowsPerPage: 10
            },
            search: ''
        }
    },
    created () {
        api.getLogs().then(response => {
            this.logs = response.data
            this.loading = false
        })
    }
}
</script>
