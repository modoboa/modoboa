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
      <v-btn class="mr-2" fab small @click="exportList" title="Export data">
        <v-icon>mdi-file-export-outline</v-icon>
      </v-btn>
      <v-btn fab small color="primary" @click="showForm = true">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
    </v-toolbar>
    <v-data-table :headers="headers" :items="domainAliases" :search="search" class="elevation-1">
      <template v-slot:item.actions="{ item }">
        <v-btn icon small title="Edit this domain alias" @click="editDomainAlias(item)">
          <v-icon>mdi-circle-edit-outline</v-icon>
        </v-btn>
        <v-btn icon small title="Remove" @click="confirmDelete(item)">
          <v-icon>mdi-delete-outline</v-icon>
        </v-btn>
      </template>
      <template v-slot:item.name="{ item }">
        {{ item.name }}
      </template>
      <template v-slot:item.dns_status="{ }">
      </template>
    </v-data-table>

  <confirm-dialog v-model="showConfirmDialog"
                  :message="deleteDomainMsg"
                  @confirm="deleteDomainAlias" />

  <v-dialog v-model="showForm"
            persistent
            max-width="800px">
    <domain-alias-form @close="closeForm" :domain-alias="selectedDomainAlias" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import DomainAliasForm from '@/components/domains/DomainAliasForm'

export default {
  components: {
    ConfirmDialog,
    DomainAliasForm
  },
  computed: mapGetters({
    domainAliases: 'domains/domainAliases'
  }),
  data () {
    return {
      headers: [
        { text: '', value: 'actions', sortable: false },
        { text: 'Name', value: 'name' },
        { text: 'Target', value: 'target.name' },
        { text: 'DNS status', value: 'dns_status', sortable: false }
      ],
      deleteDomainMsg: 'Confirm deletion?',
      showConfirmDialog: false,
      showForm: false,
      search: '',
      selectedDomainAlias: null
    }
  },
  created () {
    this.$store.dispatch('domains/getDomainAliases')
  },
  methods: {
    closeForm () {
      this.showForm = false
      this.selectedDomainAlias = null
    },
    editDomainAlias (domainAlias) {
      this.selectedDomainAlias = domainAlias
      this.showForm = true
    },
    confirmDelete (domainAlias) {
      this.selectedDomainAlias = domainAlias
      this.showConfirmDialog = true
    },
    deleteDomainAlias () {
      this.$store.dispatch('domains/deleteDomainAlias', this.selectedDomainAlias.pk)
    },
    getDNSTagType (value) {
      if (value === 'unknown') {
        return 'orange'
      }
      if (value === 'ok') {
        return 'warning'
      }
      return 'success'
    },
    exportList () {
      this.$axios.get('/domainaliases/', { headers: { Accept: 'text/csv' } }).then(resp => {
        const url = window.URL.createObjectURL(
          new Blob([resp.data], { type: 'text/csv' }))
        const link = document.createElement('a')

        link.style.display = 'none'
        link.href = url
        link.setAttribute('download', 'domain_aliases.csv')
        document.body.appendChild(link)
        link.click()
        window.URL.revokeObjectURL(link.href)
        document.body.removeChild(link)
      })
    }
  }
}
</script>
