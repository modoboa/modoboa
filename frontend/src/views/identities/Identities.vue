<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Identities</translate></v-toolbar-title>
    <v-spacer />
    <v-btn
      class="mr-2"
      :title="'Import accounts and aliases from CSV file'|translate"
      @click="showImportForm = true"
      >
      <v-icon>mdi-file-import-outline</v-icon>
    </v-btn>
    <v-btn
      class="mr-2"
      :title="'Export accounts and aliases to CSV'|translate"
      @click="exportIdentities"
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
        <v-list-item @click="showCreationWizard = true">
          <v-list-item-title><translate>Account</translate></v-list-item-title>
        </v-list-item>
        <v-list-item @click="showAliasCreationWizard = true">
          <v-list-item-title><translate>Alias</translate></v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-toolbar>
  <identity-list ref="identities" />

  <v-dialog
    v-model="showCreationWizard"
    fullscreen
    scrollable
    transition="dialog-bottom-transition"
    persistent
    >
    <account-creation-form @close="closeCreationWizard" @created="updateIdentities" />
  </v-dialog>
  <v-dialog
    v-model="showAliasCreationWizard"
    fullscreen
    scrollable
    transition="dialog-bottom-transition"
    persistent
    >
    <alias-creation-form @close="closeAliasWizard" @created="updateIdentities" />
  </v-dialog>
  <v-dialog v-model="showImportForm"
            persistent
            max-width="800px">
    <import-form
      ref="importForm"
      :title="'Import identities'|translate"
      @beforeSubmit="prepareData"
      @submit="importIdentities"
      @close="showImportForm = false"
      >
      <template v-slot:help>
        <ul>
          <li><em>account; loginname; password; first name; last name; enabled; group; address; quota; [, domain, ...]</em></li>
          <li><em>alias; address; enabled; recipient; recipient; ...</em></li>
        </ul>
      </template>
      <template v-slot:extraFields="{ form }">
        <v-switch
          v-model="form.crypt_passwords"
          :label="'Crypt passwords'|translate"
          color="primary"
          dense
          :hint="'Check this option if passwords contained in your file are not crypted'|translate"
          persistent-hint
          />
      </template>
    </import-form>
  </v-dialog>
</div>
</template>

<script>
import AccountCreationForm from '@/components/identities/AccountCreationForm'
import AliasCreationForm from '@/components/identities/AliasCreationForm'
import identities from '@/api/identities'
import IdentityList from '@/components/identities/IdentityList'
import { importExportMixin } from '@/mixins/importExport'
import ImportForm from '@/components/tools/ImportForm'

export default {
  mixins: [importExportMixin],
  components: {
    AccountCreationForm,
    AliasCreationForm,
    IdentityList,
    ImportForm
  },
  data () {
    return {
      showAliasCreationWizard: false,
      showCreationWizard: false,
      showImportForm: false
    }
  },
  methods: {
    closeAliasWizard () {
      this.showAliasCreationWizard = false
    },
    closeCreationWizard () {
      this.showCreationWizard = false
    },
    updateIdentities () {
      this.$refs.identities.fetchIdentities()
    },
    exportIdentities () {
      identities.exportAll().then(resp => {
        this.exportContent(resp.data, 'identities')
      })
    },
    prepareData (data) {
      data.append('crypt_passwords', this.form.crypt_passwords)
    },
    importIdentities (data) {
      this.importContent(identities, data)
    }
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
