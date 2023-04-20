<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Providers</translate></v-toolbar-title>
    <v-spacer />
    <v-btn
      offset-y
      color="primary"
      @click="showProviderWizard = true"
      >
      <v-icon left>mdi-plus</v-icon>
      <translate>New</translate>
    </v-btn>
  </v-toolbar>
  <providers-list />

  <v-dialog
    v-model="showProviderWizard"
    fullscreen
    scrollable
    transition="dialog-bottom-transition"
    >
    <provider-creation-form @close="showProviderWizard = false" />
      <template v-slot:help>
        <ul>
          <li><em>domain; name; quota; default mailbox quota; enabled</em></li>
          <li><em>domainalias; name; targeted domain; enabled</em></li>
        </ul>
      </template>
  </v-dialog>

</div>
</template>

<script>
import ProviderCreationForm from '@/components/imap_migration/ProviderCreationForm'
import ProvidersList from '@/components/imap_migration/ProvidersList'

export default {
  components: {
    ProviderCreationForm,
    ProvidersList
  },
  data () {
    return {
      showProviderWizard: false
    }
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
