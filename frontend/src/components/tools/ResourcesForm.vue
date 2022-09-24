<template>
<validation-observer ref="observer">
  <validation-provider
    v-for="resource in resources"
    :key="resource.name"
    v-slot="{ errors }"
    rules="required"
    >
    <label class="m-label">{{ resource.label }}</label>
    <v-text-field
      v-model="resource.max_value"
      type="number"
      outlined
      dense
      :error-messages="errors"
      @input="$emit('input', resources)"
      />
  </validation-provider>
</validation-observer>
</template>

<script>
export default {
  props: {
    value: Array
  },
  data () {
    return {
      resources: []
    }
  },
  methods: {
    async validateForm () {
      return await this.$refs.observer.validate()
    },
    getPayload () {
      return this.resources.map(r => {
        return { name: r.name, max_value: r.max_value }
      })
    }
  },
  watch: {
    value: {
      handler: function (newValue) {
        this.resources = [...newValue]
      },
      immediate: true
    }
  }
}
</script>
