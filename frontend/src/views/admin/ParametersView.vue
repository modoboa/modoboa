<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>{{ title }}</v-toolbar-title>
    </v-toolbar>

    <ParametersForm
      :key="$route.params.app"
      :app="$route.params.app"
      :structure="structure"
      :values="parameters"
      :save-function="parametersApi.saveGlobalApplication"
      @success="onSuccess"
    >
      <template
        #widget-ImageField="{
          param,
          modelValue,
          updateModelValue,
          errorMessage,
        }"
      >
        <ImageFieldWidget
          :model-value="modelValue"
          :label="param.label"
          :help-text="param.help_text"
          :uploading="!!imageState[param.name]?.uploading"
          :clearing="!!imageState[param.name]?.clearing"
          :error-message="errorMessage"
          @upload="(file) => onImageUpload(param.name, file, updateModelValue)"
          @clear="() => onImageClear(param.name, updateModelValue)"
        />
      </template>
    </ParametersForm>
  </div>
</template>

<script setup>
import parametersApi from '@/api/parameters'
import themeApi from '@/api/theme'
import { computed, reactive, ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRoute } from 'vue-router'
import { useGlobalStore, useParametersStore, useBusStore } from '@/stores'
import { useModoboaTheme } from '@/composables/theme'
import ParametersForm from '@/components/tools/ParametersForm'
import ImageFieldWidget from '@/components/tools/ImageFieldWidget'

const { $gettext } = useGettext()
const globalStore = useGlobalStore()
const { displayNotification } = useBusStore()
const route = useRoute()
const parametersStore = useParametersStore()
const { enableTheme } = useModoboaTheme()

const structure = ref([])
const parameters = ref({})
const label = ref('')

const title = computed(() => $gettext('Settings: ' + label.value))

// Per-parameter upload/clear status used by the ImageField widget slot.
const imageState = reactive({})

// Theme is currently the only consumer of ImageField. The naming convention
// `theme_<type>_logo_url` carries the backend logo_type — keeping the glue
// here means ParametersForm and the widget stay generic.
function themeLogoType(paramName) {
  const match = paramName.match(/^theme_(.+)_logo_url$/)
  return match ? match[1] : null
}

async function onImageUpload(paramName, file, updateModelValue) {
  const logoType = themeLogoType(paramName)
  if (!logoType) {
    return
  }
  imageState[paramName] = { ...imageState[paramName], uploading: true }
  try {
    const response = await themeApi.uploadLogo(logoType, file)
    updateModelValue(response.data.url)
    // Refresh the shared theme so the menu / webmail / creation-form logos
    // pick up the new URL without a page reload.
    await enableTheme()
    displayNotification({ msg: $gettext('Image uploaded') })
  } catch (error) {
    displayNotification({
      msg: $gettext('Could not upload image'),
      type: 'error',
    })
  } finally {
    imageState[paramName] = { ...imageState[paramName], uploading: false }
  }
}

async function onImageClear(paramName, updateModelValue) {
  const logoType = themeLogoType(paramName)
  if (!logoType) {
    return
  }
  imageState[paramName] = { ...imageState[paramName], clearing: true }
  try {
    await themeApi.clearLogo(logoType)
    updateModelValue('')
    await enableTheme()
    displayNotification({ msg: $gettext('Image removed') })
  } catch (error) {
    displayNotification({
      msg: $gettext('Could not remove image'),
      type: 'error',
    })
  } finally {
    imageState[paramName] = { ...imageState[paramName], clearing: false }
  }
}

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
