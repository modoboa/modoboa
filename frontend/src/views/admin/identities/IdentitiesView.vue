<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ $gettext('Identities') }}</v-toolbar-title>
    </v-toolbar>

    <IdentityList>
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
            <v-list-item @click="showCreationWizard = true">
              <v-list-item-title>{{ $gettext('Account') }}</v-list-item-title>
            </v-list-item>
            <v-list-item @click="showAliasCreationWizard = true">
              <v-list-item-title>{{ $gettext('Alias') }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <v-btn
          class="mr-2"
          :title="$gettext('Import accounts and aliases from CSV file')"
          variant="flat"
          icon="mdi-file-import-outline"
          @click="showImportForm = true"
        ></v-btn>
        <v-btn
          class="mr-2"
          :title="$gettext('Export accounts and aliases to CSV')"
          icon="mdi-file-export-outline"
          variant="flat"
          @click="exportIdentities"
        ></v-btn>
      </template>
    </IdentityList>
    <v-dialog
      v-model="showAliasCreationWizard"
      fullscreen
      scrollable
      z-index="10"
    >
      <AliasCreationForm @close="showAliasCreationWizard = false" />
    </v-dialog>

    <v-dialog v-model="showCreationWizard" fullscreen scrollable z-index="10">
      <AccountCreationForm @close="showCreationWizard = false" />
    </v-dialog>

    <v-dialog v-model="showImportForm" persistent max-width="800px">
      <ImportForm
        ref="importForm"
        :title="$gettext('Import identities')"
        @submit="importIdentities"
        @close="showImportForm = false"
      >
        <template #help>
          <ul>
            <li>
              <em
                >account; loginname; password; first name; last name; enabled;
                group; address; quota; [, domain, ...]</em
              >
            </li>
            <li>
              <em
                >alias; address; enabled; recipient; [more recipients; ...]</em
              >
            </li>
          </ul>
        </template>
        <template #extraFields="{ form }">
          <v-switch
            v-model="form.crypt_passwords"
            :label="$gettext('Crypt passwords')"
            color="primary"
            density="compact"
            :hint="
              $gettext(
                'Check this option if passwords contained in your file are not crypted'
              )
            "
            persistent-hint
          />
        </template>
      </ImportForm>
    </v-dialog>
  </div>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import identitiesApi from '@/api/identities'
import IdentityList from '@/components/admin/identities/IdentityList.vue'
import AliasCreationForm from '@/components/admin/identities/AliasCreationForm.vue'
import AccountCreationForm from '@/components/admin/identities/AccountCreationForm.vue'
import ImportForm from '@/components/tools/ImportForm'
import { importExportMixin } from '@/mixins/importExport'

const { $gettext } = useGettext()
const { importContent, exportContent } = importExportMixin()

const showCreationWizard = ref(false)
const showAliasCreationWizard = ref(false)
const showImportForm = ref(false)
const importForm = ref()

function exportIdentities() {
  identitiesApi.exportAll().then((resp) => {
    exportContent(resp.data, 'identities', $gettext)
  })
}

function importIdentities(data, form) {
  data.append('crypt_passwords', form.crypt_passwords)
  importContent(identitiesApi, data, importForm, $gettext)
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
