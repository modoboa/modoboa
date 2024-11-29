<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ title }}</v-toolbar-title>
    </v-toolbar>

    <v-tabs v-model="active" bg-color="white">
      <v-tab
        v-for="(element, index) in displayableElements"
        :key="index"
        color="primary"
        :class="tab_error.includes(index) ? 'error_tab' : ''"
      >
        {{ element.label }}
      </v-tab>
    </v-tabs>
    <v-tabs-window v-model="active">
      <v-tabs-window-item
        v-for="element in displayableElements"
        :key="element.label"
      >
        <v-container fluid class="pa-0">
          <v-card>
            <v-card-text>
              <template
                v-for="param in displayableParams(element.parameters)"
                :key="param.name"
              >
                <div class="my-4">
                  <template v-if="param.widget === 'SeparatorField'">
                    <h2>{{ param.label }}</h2>
                  </template>
                  <template v-else-if="param.widget === 'BooleanField'">
                    <v-switch
                      v-if="param.widget === 'BooleanField'"
                      v-model="parameters[param.name]"
                      :label="param.label"
                      :hint="param.help_text"
                      :error="formErrors[param.name] !== undefined"
                      color="primary"
                      density="compact"
                      :error-messages="formErrors[param.name]"
                      persistent-hint
                    />
                  </template>
                  <template v-else>
                    <label class="m-label">{{ param.label }}</label>
                    <v-select
                      v-if="param.widget === 'ChoiceField'"
                      v-model="parameters[param.name]"
                      :items="param.choices"
                      item-title="text"
                      :hint="param.help_text"
                      persistent-hint
                      density="compact"
                      variant="outlined"
                    />
                    <v-text-field
                      v-else
                      v-model="parameters[param.name]"
                      :hint="param.help_text"
                      persistent-hint
                      :error="formErrors[param.name] !== undefined"
                      :error-messages="formErrors[param.name]"
                      :type="
                        param.widget === 'PasswordField' ? 'password' : 'text'
                      "
                      density="compact"
                      variant="outlined"
                    />
                  </template>
                </div>
              </template>
            </v-card-text>
          </v-card>
        </v-container>
      </v-tabs-window-item>
    </v-tabs-window>
    <v-btn
      icon="mdi-content-save"
      class="ma-5"
      position="fixed"
      location="bottom right"
      color="green"
      size="large"
      @click="save"
    />
  </div>
</template>

<script setup lang="js">
import { useBusStore } from '@/stores'
import parametersApi from '@/api/parameters'
import { ref, computed, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute } from 'vue-router'
import { useGlobalStore, useParametersStore } from '@/stores'

const { $gettext } = useGettext()
const busStore = useBusStore()
const globalStore = useGlobalStore()
const route = useRoute()
const parametersStore = useParametersStore()

const active = ref(0)
const structure = ref([])
const parameters = ref({})
const formErrors = ref({})
const label = ref('')
const tab_error = ref([])

const displayableElements = computed(() =>
  structure.value.filter((element) => display(element))
)

const title = computed(() => $gettext('Settings: ' + label.value))

function loadParams(app) {
  parametersApi.getApplicationStructure(app).then((response) => {
    structure.value = response.data
  })
  parametersApi.getApplication(app).then((response) => {
    parameters.value = response.data.params
    label.value = response.data.label
  })
}

function display(element) {
  if (element.display === '') {
    return true
  }
  let result = true
  element.display.split('&').forEach((rule) => {
    let [field, value] = rule.split('=')
    if (value === 'true' || value === 'false') {
      value = Boolean(value)
    }
    result &= parameters.value[field] === value
  })
  return result
}

function displayableParams(params) {
  return params.filter((param) => display(param))
}

async function save() {
  formErrors.value = {}
  tab_error.value = []
  parametersApi
    .saveApplication(route.params.app, parameters.value)
    .then(() => {
      busStore.displayNotification({
        msg: $gettext('Parameters updated'),
      })
      globalStore.fetchNotifications()
      if (route.params.app === 'imap_migration') {
        parametersStore.imapMigrationEnabled =
          parameters.value.enabled_imapmigration
      }
    })
    .catch((error) => {
      busStore.displayNotification({
        msg: $gettext('Could not save parameters'),
        type: 'error',
      })
      formErrors.value = error.response.data
      Object.keys(formErrors.value).forEach((element) => {
        for (let i = 0; i < structure.value.length; i++) {
          const isIn =
            structure.value[i].parameters.filter(
              (param) => param.name === element
            ).length > 0
          if (isIn) {
            tab_error.value.push(i)
          }
        }
      })
    })
}

watch(route, (toRoute) => {
  loadParams(toRoute.params.app)
})

watch(parameters, () => {
  tab_error.value = []
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
