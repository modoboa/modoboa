<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Domains</translate></v-toolbar-title>
    <v-spacer />
    <v-btn
      class="mr-2"
      :title="'Import domains and aliases from CSV file'|translate"
      @click="showImportForm = true"
      >
      <v-icon>mdi-file-import-outline</v-icon>
    </v-btn>
    <v-btn
      class="mr-2"
      :title="'Export domains and aliases to CSV'|translate"
      @click="exportDomains"
      >
      <v-icon>mdi-file-export-outline</v-icon>
    </v-btn>
    <v-menu offset-y>
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primary" v-bind="attrs" v-on="on">
          <v-icon left>mdi-plus</v-icon>
          <translate>New</translate>
        </v-btn>
      </template>
      <v-list dense>
        <v-list-item @click="showDomainWizard = true">
          <v-list-item-title><translate>Domain</translate></v-list-item-title>
        </v-list-item>
        <v-list-item @click="showAliasForm = true">
          <v-list-item-title><translate>Alias</translate></v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-toolbar>
  <domain-list />

  <v-dialog
    v-model="showDomainWizard"
    fullscreen
    scrollable
    transition="dialog-bottom-transition"
    >
    <domain-creation-form @close="showDomainWizard = false" />
  </v-dialog>
  <v-dialog v-model="showAliasForm"
            persistent
            max-width="800px">
    <domain-alias-form @close="showAliasForm = false" />
  </v-dialog>
  <v-dialog v-model="showImportForm"
            persistent
            max-width="800px">
    <import-form
      ref="importForm"
      :title="'Import domains'|translate"
      @submit="importDomains"
      @close="showImportForm = false"
      >
      <template v-slot:help>
        <ul>
          <li><em>domain; name; quota; default mailbox quota; enabled</em></li>
          <li><em>domainalias; name; targeted domain; enabled</em></li>
          <li><em>relaydomain; name; target host; target port; service; enabled; verify recipients</em></li>
        </ul>
      </template>
    </import-form>
  </v-dialog>

</div>
</template>

<script>
import domains from '@/api/domains'
import DomainAliasForm from '@/components/domains/DomainAliasForm'
import DomainCreationForm from '@/components/domains/DomainCreationForm'
import DomainList from '@/components/domains/DomainList'
import { importExportMixin } from '@/mixins/importExport'
import ImportForm from '@/components/tools/ImportForm'

export default {
  mixins: [importExportMixin],
  components: {
    DomainAliasForm,
    DomainCreationForm,
    DomainList,
    ImportForm
  },
  data () {
    return {
      showAliasForm: false,
      showDomainWizard: false,
      showImportForm: false
    }
  },
  methods: {
    exportDomains () {
      domains.exportAll().then(resp => {
        this.exportContent(resp.data, 'domains')
      })
    },
    importDomains (data) {
      this.importContent(domains, data)
    }
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
