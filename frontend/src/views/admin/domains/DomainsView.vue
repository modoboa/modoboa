<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Domains') }}</v-toolbar-title>
    </v-toolbar>

    <DomainList>
      <template #extraActions>
        <v-menu offset-y>
          <template #activator="{ props }">
            <v-btn
              color="primary"
              variant="outlined"
              v-bind="props"
              prepend-icon="mdi-plus"
              class="mr-4"
            >
              {{ $gettext('New') }}
            </v-btn>
          </template>
          <v-list density="compact">
            <v-list-item @click="showDomainWizard = true">
              <v-list-item-title>{{ $gettext('Domain') }}</v-list-item-title>
            </v-list-item>
            <v-list-item @click="showAliasForm = true">
              <v-list-item-title>{{ $gettext('Alias') }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          class="mr-2"
          :title="$gettext('Import domains and aliases from CSV file')"
          variant="flat"
          icon="mdi-file-import-outline"
          @click="showImportForm = true"
        ></v-btn>
        <v-btn
          class="mr-2"
          :title="$gettext('Export domains and aliases to CSV')"
          variant="flat"
          icon="mdi-file-export-outline"
          @click="exportDomains"
        ></v-btn>
      </template>
    </DomainList>

    <v-dialog v-model="showDomainWizard" fullscreen scrollable z-index="10">
      <DomainCreationForm @close="showDomainWizard = false" />
    </v-dialog>
    <v-dialog v-model="showAliasForm" persistent max-width="800px">
      <DomainAliasForm @close="showAliasForm = false" />
    </v-dialog>
    <v-dialog v-model="showImportForm" persistent max-width="800px">
      <ImportForm
        ref="importForm"
        :title="$gettext('Import domains')"
        @submit="importDomains"
        @close="showImportForm = false"
      >
        <template #help>
          <ul>
            <li>
              <em>domain; name; quota; default mailbox quota; enabled</em>
            </li>
            <li>
              <em>domainalias; name; targeted domain; enabled</em>
            </li>
            <li>
              <em
                >relaydomain; name; target host; target port; service; enabled;
                verify recipients</em
              >
            </li>
          </ul>
        </template>
      </ImportForm>
    </v-dialog>
  </div>
</template>

<script setup lang="js">
import { ref } from 'vue'
import domainApi from '@/api/domains'
import { useGettext } from 'vue3-gettext'
import DomainAliasForm from '@/components/admin/domains/DomainAliasForm'
import DomainCreationForm from '@/components/admin/domains/DomainCreationForm'
import DomainList from '@/components/admin/domains/DomainList'
import ImportForm from '@/components/tools/ImportForm'
import { importExportMixin } from '@/mixins/importExport'

const showAliasForm = ref(false)
const showDomainWizard = ref(false)
const showImportForm = ref(false)

const { $gettext } = useGettext()

const importForm = ref()

const { importContent, exportContent } = importExportMixin()

function exportDomains() {
  domainApi.exportAll().then((resp) => {
    exportContent(resp.data, 'domains', $gettext)
  })
}

function importDomains(data) {
  importContent(domainApi, data, importForm, $gettext)
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}

.v-tabs-items {
  background-color: #f7f8fa !important;
}
</style>
