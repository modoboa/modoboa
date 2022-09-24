<template>
<div>
  <validation-observer ref="observer">
    <label class="m-label"><translate>Service</translate></label>
    <validation-provider
      v-slot="{ errors }"
      rules="required"
      >
      <v-autocomplete
        v-model="service"
        :items="backends"
        item-text="name"
        return-object
        outlined
        @change="resetForm"
        :error-messages="errors"
        />
    </validation-provider>
    <template v-if="service">
      <template v-for="setting in service.settings">
        <div :key="setting.name">
          <validation-provider
            v-slot="{ errors }"
            :rules="setting.required ? 'required' : ''"
            >
            <template
              v-if="setting.type === 'str' || setting.type === 'int'"
              >
              <label class="m-label">{{ setting.label }}</label>
              <v-text-field
                v-model="form.transport.settings[`${service.name}_${setting.name}`]"
                outlined
                :error-messages="errors"
                :type="setting.type === 'int' ? 'number' : 'text'"
                @input="update"
                />
            </template>
            <v-checkbox
              v-else-if="setting.type === 'boolean'"
              v-model="form.transport.settings[`${service.name}_${setting.name}`]"
              :label="setting.label"
              :error-messages="errors"
              @change="update"
              />
          </validation-provider>
        </div>
      </template>
    </template>
  </validation-observer>
</div>
</template>

<script>
import transports from '@/api/transports'

export default {
  props: {
    value: Object
  },
  data () {
    return {
      backends: [],
      form: {},
      service: null
    }
  },
  methods: {
    resetForm (value) {
      this.$set(this.form, 'transport', { service: value.name, settings: {} })
      for (const setting of value.settings) {
        if (setting.default) {
          let defaultValue = setting.default
          if (setting.type === 'int') {
            defaultValue = parseInt(defaultValue)
          } else if (setting.type === 'boolean') {
            if (defaultValue === 'False') {
              defaultValue = false
            } else {
              defaultValue = true
            }
          }
          this.$set(this.form.transport.settings, `${value.name}_${setting.name}`, defaultValue)
          this.update()
        }
      }
    },
    checkSettingTypes (data) {
      for (const setting of this.service.settings) {
        if (setting.type === 'int') {
          const fullName = `${this.service.name}_${setting.name}`
          data.transport.settings[fullName] = parseInt(data.transport.settings[fullName])
        }
      }
    },
    update () {
      this.$emit('input', this.form)
    }
  },
  mounted () {
    this.form = { ...this.value }
    transports.getAll().then(resp => {
      this.backends = resp.data
      if (this.value) {
        this.service = this.backends.find(backend => backend.name === this.form.transport.service)
      }
    })
  },
  watch: {

  }
}
</script>
