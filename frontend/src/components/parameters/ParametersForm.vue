<template>
<v-layout>
  <v-flex>
    <v-tabs v-model="active">
      <v-tab v-for="(element, index) in displayableElements"
             :key="index"
             >
        {{ element.label }}
      </v-tab>
      <v-tabs-items v-model="active">
        <v-tab-item
          v-for="(element, index) in displayableElements"
          :key="index"
          >
          <v-card>
            <v-card-text>
              <template v-for="(param, index) in displayableParams(element.parameters)">
                <div class="my-4" :key="index">
                <template v-if="param.widget === 'BooleanField'">
                  <v-switch
                    v-model="parameters[param.name]"
                    :label="param.label"
                    :hint="param.help_text"
                    persistent-hint
                    v-if="param.widget === 'BooleanField'"
                    />
                </template>
                <template v-else>
                  <label class="m-label">{{ param.label }}</label>
                  <v-select
                    v-model="parameters[param.name]"
                    :items="param.choices"
                    :hint="param.help_text"
                    persistent-hint
                    v-if="param.widget === 'ChoiceField'"
                    dense
                    outlined
                    />
                  <v-text-field
                    :hint="param.help_text"
                    persistent-hint
                    v-model="parameters[param.name]"
                    :error="formErrors[param.name] !== undefined"
                    :error-messages="formErrors[param.name]"
                    v-else
                    dense
                    outlined
                    />
                </template>
                </div>
              </template>
            </v-card-text>
          </v-card>
        </v-tab-item>
      </v-tabs-items>
    </v-tabs>
    <v-btn fixed
           dark
           fab
           bottom
           right
           color="green"
           @click="save"
           >
      <v-icon>mdi-content-save</v-icon>
    </v-btn>
  </v-flex>
</v-layout>
</template>

<script>
import { bus } from '@/main'
import parameters from '@/api/parameters'

export default {
  data () {
    return {
      active: 0,
      structure: [],
      parameters: {},
      formErrors: {}
    }
  },
  computed: {
    displayableElements () {
      const result = this.structure.filter(element => this.display(element))
      return result
    }
  },
  created () {
    this.loadParams(this.$route.params.app)
  },
  watch: {
    '$route' (to, from) {
      this.loadParams(to.params.app)
    }
  },
  methods: {
    loadParams (app) {
      parameters.getApplicationStructure(app).then(response => {
        this.structure = response.data
      })
      parameters.getApplication(app).then(response => {
        this.parameters = response.data
      })
    },
    display (element) {
      if (element.display === '') {
        return true
      }
      var [field, value] = element.display.split('=')
      if (value === 'true' || value === 'false') {
        value = Boolean(value)
      }
      return this.parameters[field] === value
    },
    displayableParams (params) {
      return params.filter(param => this.display(param))
    },
    save () {
      parameters.saveApplication(this.$route.params.app, this.parameters).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Parameters updated') })
      }).catch(error => {
        this.formErrors = error.response.data
      })
    }
  }
}
</script>
