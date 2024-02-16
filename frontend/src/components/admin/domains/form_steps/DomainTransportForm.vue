<template>
  <v-form ref="vFormRef">
    <label class="m-label">{{ $gettext('Service') }}</label>
    <v-autocomplete
      v-model="service"
      :items="backends"
      item-title="name"
      return-object
      variant="outlined"
      :rules="[rules.required]"
    />
    <template v-if="service">
      <template v-for="(setting, i) in service.settings" :key="i">
        <template v-if="setting.type === 'str' || setting.type === 'int'">
          <label class="m-label">{{ setting.label }}</label>
          <v-text-field
            v-model="form.settings[`${service.name}_${setting.name}`]"
            variant="outlined"
            :type="form.type === 'int' ? 'number' : 'text'"
            :rules="[!!setting.required || rules.required]"
            @update:model-value="update"
          />
        </template>
        <v-checkbox
          v-else-if="setting.type === 'boolean'"
          v-model="form.settings[`${service.name}_${setting.name}`]"
          :label="setting.label"
          @update:model-value="update"
        />
      </template>
    </template>
  </v-form>
</template>

<script setup lang="js">
import transports from '@/api/transports'
import { useGettext } from 'vue3-gettext'
import { ref, onMounted } from 'vue'
import rules from '@/plugins/rules.js'

const { $gettext } = useGettext()

const props = defineProps({ modelValue: { type: Object, default: () => {} } })
const emit = defineEmits(['update:modelValue'])
const vFormRef = ref()
const form = ref({})
const service = ref()
const backends = ref([])

function checkSettingTypes(data) {
  for (const setting of service.value.settings) {
    if (setting.type === 'int') {
      const fullName = `${service.value.name}_${setting.name}`
      data.transport.settings[fullName] = parseInt(
        data.transport.settings[fullName]
      )
    }
  }
}

function update() {
  form.value.service = service.value.name
  emit('update:modelValue', form.value)
}

onMounted(() => {
  form.value = { ...props.modelValue }
  transports.getAll().then((resp) => {
    backends.value = resp.data
    if (form.value.service) {
      service.value = backends.value.find(
        (backend) => backend.name === form.value.service
      )
    }
  })
})

defineExpose({ checkSettingTypes, service, vFormRef })
</script>
