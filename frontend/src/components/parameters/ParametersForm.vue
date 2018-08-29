<template>
  <v-layout>
    <v-flex>
      <h1 class="title">Parameters</h1>
      <v-expansion-panel>
        <v-expansion-panel-content
            v-for="(element, index) in structure"
            :key="index"
        >
          <div slot="header">{{ element.label }}</div>
          <v-card>
            <v-card-text>
              <v-text-field v-for="(param, index) in element.parameters"
                            :label="param.label"
                            :key="index"
                            :hint="param.help_text"
                            v-model="parameters[param.name]"
                            v-if="param.widget === 'CharField' || param.widget === 'IntegerField'">
              </v-text-field>
              <v-checkbox :label="param.label"
                          v-model="parameters[param.name]"
                          v-else-if="param.widget === 'BooleanField'"
              >
              </v-checkbox>
              <v-select :label="param.label"
                        v-model="parameters[param.name]"
                        :items="param.choices"
                        v-else-if="param.widget === 'ChoiceField'">
              </v-select>
            </v-card-text>
          </v-card>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-flex>
  </v-layout>
</template>

<script>
import * as api from '@/api'

export default {
    data () {
        return {
            structure: [],
            parameters: {}
        }
    },
    created () {
        api.getParametersStructure().then(response => {
            this.structure = response.data
        })
        api.getParameters().then(response => {
            this.parameters = response.data
        })
    }
}
</script>
