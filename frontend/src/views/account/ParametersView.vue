<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ title }}</v-toolbar-title>
    </v-toolbar>

    <ParametersForm
      :app="$route.params.app"
      :structure="structure"
      :values="parameters"
      :save-function="parametersApi.saveUserApplication"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute } from 'vue-router'
import ParametersForm from '@/components/tools/ParametersForm'
import parametersApi from '@/api/parameters'

const { $gettext } = useGettext()
const route = useRoute()

const label = ref('')
const structure = ref([])
const parameters = ref({})

const title = computed(() => $gettext('Settings: ' + label.value))

function loadParams(app) {
  parametersApi.getUserApplicationStructure(app).then((response) => {
    structure.value = response.data
  })
  parametersApi.getUserApplication(app).then((response) => {
    parameters.value = response.data.params
    label.value = response.data.label
  })
}

loadParams(route.params.app)
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>

<style>
.v-window__container {
  width: 100% !important;
}
</style>
