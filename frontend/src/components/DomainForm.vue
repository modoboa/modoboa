<template>
  <div>
    <h1 class="title">Add domain</h1>
    <form>
      <b-field label="Name">
        <b-input v-model="domain.name"></b-input>
      </b-field>
      <b-field label="Quota">
        <b-input v-model="domain.quota"></b-input>
      </b-field>
      <b-field>
        <button class="button is-primary" @click="saveDomain">Save</button>
      </b-field>
    </form>
  </div>
</template>

<script>
import * as api from '@/api'

export default {
    data () {
        return {
            domain: {}
        }
    },
    methods: {
        saveDomain () {
            api.createDomain(this.domain).then(response => {
            })
        }
    }
}
</script>
