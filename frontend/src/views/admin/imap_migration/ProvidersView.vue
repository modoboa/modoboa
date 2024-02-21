<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title> {{ $gettext('Providers') }} </v-toolbar-title>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        prepend-icon="mdi-plus"
        @click="showProviderWizard = true"
      >
        {{ $gettext('New') }}
      </v-btn>
    </v-toolbar>

    <ProvidersList />

    <v-dialog
      v-model="showProviderWizard"
      fullscreen
      scrollable
      transition="dialog-bottom-transition"
    >
      <ProviderCreationForm @close="showProviderWizard = false" />
    </v-dialog>
  </div>
</template>

<script setup lang="js">
import ProviderCreationForm from '@/components/admin/imap_migration/ProviderCreationForm'
import ProvidersList from '@/components/admin/imap_migration/ProvidersList'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()

const showProviderWizard = ref(false)
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
