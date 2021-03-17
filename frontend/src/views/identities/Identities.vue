<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>Identities</translate></v-toolbar-title>
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
          <v-icon left>mdi-plus</v-icon>
          <translate>New</translate>
        </v-btn>
      </template>
      <v-list dense>
        <v-list-item @click="showCreationWizard = true">
          <v-list-item-title><translate>Account</translate></v-list-item-title>
        </v-list-item>
        <v-list-item @click="showAliasForm = true">
          <v-list-item-title><translate>Alias</translate></v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-toolbar>
  <identity-list />

  <v-dialog
    v-model="showCreationWizard"
    fullscreen
    scrollable
    transition="dialog-bottom-transition"
    >
    <account-creation-form @close="closeCreationWizard" />
  </v-dialog>
</div>
</template>

<script>
import AccountCreationForm from '@/components/identities/AccountCreationForm'
import IdentityList from '@/components/identities/IdentityList'

export default {
  components: {
    AccountCreationForm,
    IdentityList
  },
  data () {
    return {
      showCreationWizard: false
    }
  },
  methods: {
    closeCreationWizard () {
      this.showCreationWizard = false
    }
  }
}
</script>
