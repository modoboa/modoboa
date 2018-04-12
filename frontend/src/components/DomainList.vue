<template>
  <div>
    <div class="columns">
      <div class="column">
        <h1 class="title">Domains</h1>
      </div>
      <div class="column">
        <router-link :to="{ name: 'DomainAdd' }">Add</router-link>
      </div>
    </div>
    <b-table :data="domains" checkable>
      <template slot-scope="props">
        <b-table-column field="name" label="Name">
          {{ props.row.name }}
        </b-table-column>
        <b-table-column field="quota" label="Quota">
          <progress class="progress is-primary">30%</progress>
        </b-table-column>
      </template>
    </b-table>
  </div>
</template>

<script>
import * as api from '@/api'

export default {
    data () {
        return {
            domains: [],
            columns: [
                {
                    field: 'name',
                    label: 'Name'
                },
                {
                    field: 'quota',
                    label: 'Quota'
                }
            ]
        }
    },
    created () {
        api.getDomains().then(response => {
            this.domains = response.data
        })
    }
}
</script>
