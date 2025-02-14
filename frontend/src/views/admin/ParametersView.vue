<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ title }}</v-toolbar-title>
    </v-toolbar>

    <ParametersForm
      :app="$route.params.app"
      :structure="structure"
      :values="parameters"
      :save-function="parametersApi.saveGlobalApplication"
      @success="onSuccess"
    />
  </div>
</template>

<script setup>
import { useBusStore } from '@/stores'
import parametersApi from '@/api/parameters'
import { ref, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute } from 'vue-router'
import { useGlobalStore, useParametersStore } from '@/stores'
import ParametersForm from '@/components/tools/ParametersForm'

const { $gettext } = useGettext()
const globalStore = useGlobalStore()
const route = useRoute()
const parametersStore = useParametersStore()

const structure = ref([])
const parameters = ref({})
const label = ref('')

const title = computed(() => $gettext('Settings: ' + label.value))

function loadParams(app) {
  parametersApi.getGlobalApplicationStructure(app).then((response) => {
    structure.value = response.data
  })
  parametersApi.getGlobalApplication(app).then((response) => {
    parameters.value = response.data.params
    label.value = response.data.label
  })
}

function onSuccess(newValues) {
  globalStore.fetchNotifications()
  if (route.params.app === 'imap_migration') {
    parametersStore.imapMigrationEnabled = newValues.enabled_imapmigration
  }
}

watch(route, (toRoute) => {
  loadParams(toRoute.params.app)
})

loadParams(route.params.app)
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
.error_tab {
  color: #ff5252 !important;
}
</style>

<style>
.v-window__container {
  width: 100% !important;
}
</style>
