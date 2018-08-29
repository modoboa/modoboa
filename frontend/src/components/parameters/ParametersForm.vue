<template>
  <v-layout row wrap>
    <v-flex>
      <h1>Parameters</h1>
      <v-tabs v-model="active">
        <v-tab v-for="(element, index) in structure"
               :key="index"

               v-if="display(element)"
        >
          {{ element.label }}
        </v-tab>
        <v-tabs-items>
          <v-tab-item
              v-for="(element, index) in structure"
              :key="index"
              v-if="display(element)"
          >
            <v-card>
              <v-card-text>
                <v-text-field v-for="(param, index) in element.parameters"
                              :label="param.label"
                              :key="index"
                              :hint="param.help_text"
                              v-model="parameters[param.name]"
                              :error="formErrors[param.name] !== undefined"
                              :error-messages="formErrors[param.name]"
                              v-if="(param.widget === 'CharField' || param.widget === 'IntegerField') && display(param)">
                </v-text-field>
                <v-checkbox :label="param.label"
                            v-model="parameters[param.name]"
                            v-else-if="param.widget === 'BooleanField' && display(param)"
                >
                </v-checkbox>
                <v-select :label="param.label"
                          v-model="parameters[param.name]"
                          :items="param.choices"
                          v-else-if="param.widget === 'ChoiceField' && display(param)">
                </v-select>
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
        <v-icon>save</v-icon>
      </v-btn>
    </v-flex>
  </v-layout>
</template>

<script>
import * as api from '@/api'

export default {
    data () {
        return {
            active: 0,
            structure: [],
            parameters: {},
            formErrors: {}
        }
    },
    created () {
        var app = this.$route.params.app
        api.getParametersStructure(app).then(response => {
            this.structure = response.data
        })
        api.getParametersForApplication(app).then(response => {
            this.parameters = response.data
        })
    },
    methods: {
        display (element) {
            if (element.display === '') {
                return true
            }
            var [field, value] = element.display.split('=')
            return this.parameters[field] === value
        },
        save () {
            api.saveParametersForApplication(
                this.$route.params.app, this.parameters
            ).then(response => {
            }, response => {
                this.formErrors = response.data
            })
        }
    }
}
</script>
