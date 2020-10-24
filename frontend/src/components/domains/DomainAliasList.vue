<template>
  <div>
    <v-toolbar flat color="white">
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
        ></v-text-field>
      <v-spacer></v-spacer>
      <v-btn class="mr-2" fab small>
        <v-icon>mdi-file-import-outline</v-icon>
      </v-btn>
      <v-btn class="mr-2" fab small>
        <v-icon>mdi-file-export-outline</v-icon>
      </v-btn>
    </v-toolbar>
    <v-data-table :headers="headers" :items="domainAliases" :search="search" class="elevation-1">
      <template v-slot:item.actions="{ item }">
        <v-btn icon small :to="{ name: 'DomainEdit', params: { domainPk: item.pk }}">
          <v-icon>mdi-circle-edit-outline</v-icon>
        </v-btn>
        <v-btn icon small title="Remove" @click="confirmDelete(item)">
          <v-icon>mdi-delete-outline</v-icon>
        </v-btn>
      </template>
      <template v-slot:item.name="{ item }">
        <router-link :to="{ name: 'DomainDetail', params: { pk: item.pk } }">
          {{ item.name }}
        </router-link>
      </template>
      <template v-slot:item.dns_status="{ }">
      </template>
    </v-data-table>

  <confirm-dialog v-model="showConfirmDialog"
                  :message="deleteDomainMsg"
                  @confirm="deleteDomain" />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  components: {
    ConfirmDialog
  },
  computed: mapGetters({
    domainAliases: 'domains/domainAliases'
  }),
  data () {
    return {
      headers: [
        { text: '', value: 'actions', sortable: false },
        { text: 'Name', value: 'name' },
        { text: 'DNS status', value: 'dns_status', sortable: false }
      ],
      deleteDomainMsg: 'Confirm deletion?',
      selectedDomain: null,
      showConfirmDialog: false,
      search: ''
    }
  },
  created () {
    this.$store.dispatch('domains/getDomainAliases')
  },
  methods: {
    confirmDelete (domain) {
      this.selectedDomain = domain
      this.showConfirmDialog = true
    },
    deleteDomain () {

    },
    getDNSTagType (value) {
      if (value === 'unknown') {
        return 'orange'
      }
      if (value === 'ok') {
        return 'warning'
      }
      return 'success'
    }
  }
}
</script>
