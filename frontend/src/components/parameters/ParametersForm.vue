<template>
  <div>
    <h1 class="title">Parameters</h1>
    <form>
      <h2 class="subtitle" v-for="(element, index) in structure"
          v-if="element.type === 'section'" :key="index">
        {{ element.label }}
      </h2>
      <b-field v-else :label="element.label" horizontal>
        <b-input v-if="element.widget === 'CharField' || element.widget === 'IntegerField'"
                 v-model="parameters[element.name]">
        </b-input>
        <b-checkbox v-else-if="element.widget === 'BooleanField'"
                    v-model="parameters[element.name]"></b-checkbox>
        <b-select v-else-if="element.widget === 'ChoiceField'"
                  v-model="parameters[element.name]">
          <option v-for="choice in Object.entries(element.choices)"
                  :value="choice[0]" :key="choice[0]">
            {{ choice[1] }}
          </option>
        </b-select>
      </b-field>
    </form>
  </div>
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
