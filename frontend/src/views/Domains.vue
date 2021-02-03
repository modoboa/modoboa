<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Domains</translate></v-toolbar-title>
    <v-spacer />
    <v-btn class="mr-2">
      <v-icon>mdi-file-import-outline</v-icon>
    </v-btn>
    <v-btn class="mr-2">
      <v-icon>mdi-file-export-outline</v-icon>
    </v-btn>
    <v-menu offset-y>
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primary" v-bind="attrs" v-on="on">
          <v-icon left>mdi-plus</v-icon> <translate>New</translate>
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
</div>
</template>

<script>
import DomainAliasForm from '@/components/domains/DomainAliasForm'
import DomainCreationForm from '@/components/domains/DomainCreationForm'
import DomainList from '@/components/domains/DomainList'

export default {
  components: {
    DomainAliasForm,
    DomainCreationForm,
    DomainList
  },
  data () {
    return {
      showAliasForm: false,
      showDomainWizard: false
    }
  },
  methods: {

  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
