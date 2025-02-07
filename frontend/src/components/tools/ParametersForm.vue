<template>
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
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'

const props = defineProps({
  app: {
    type: String,
    default: '',
  },
  structure: {
    type: Array,
    default: null,
  },
  values: {
    type: Object,
    default: null,
  },
  saveFunction: {
    type: Function,
    default: null,
  },
})
const emit = defineEmits(['success'])

const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const displayableElements = computed(() =>
  props.structure.filter((element) => display(element))
)

const active = ref(0)
const formErrors = ref({})
const parameters = ref({})
const tab_error = ref([])

watch(
  () => props.values,
  (newValue) => {
    if (newValue) {
      parameters.value = { ...newValue }
    }
  }
)
watch(parameters, () => {
  tab_error.value = []
})

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
  try {
    await props.saveFunction(props.app, parameters.value)
    displayNotification({
      msg: $gettext('Parameters updated'),
    })
    emit('success', parameters.value)
  } catch (error) {
    displayNotification({
      msg: $gettext('Could not save parameters'),
      type: 'error',
    })
    formErrors.value = error.response.data
    Object.keys(formErrors.value).forEach((element) => {
      for (let i = 0; i < props.structure.length; i++) {
        const isIn =
          props.structure[i].parameters.filter(
            (param) => param.name === element
          ).length > 0
        if (isIn) {
          tab_error.value.push(i)
        }
      }
    })
  }
}
</script>

<style scoped>
.error_tab {
  color: #ff5252 !important;
}
</style>
