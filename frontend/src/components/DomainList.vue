<template>
  <div>
    <div class="columns">
      <div class="column">
        <h1 class="title">Domains</h1>
      </div>
      <div class="column">
        <router-link :to="{ name: 'DomainAdd' }" class="button is-primary">Add</router-link>
      </div>
    </div>
    <b-table :data="domains" checkable>
      <template slot-scope="props">
        <b-table-column>
          <router-link :to="{ name: 'DomainEdit', params: { domainPk: props.row.pk }}">
            <b-icon icon="pencil"></b-icon>
          </router-link>
        </b-table-column>
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
import { mapGetters } from 'vuex'

export default {
    computed: mapGetters([
        'domains'
    ]),
    data () {
        return {
            columns: [
                {},
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
        this.$store.dispatch('getDomains')
    }
}
</script>
