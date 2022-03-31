<template>
<validation-observer ref="observer">
  <validation-provider
    v-for="resource in account.resources"
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
      />
  </validation-provider>
</validation-observer>
</template>

<script>
export default {
  props: {
    account: Object
  },
  methods: {
    async validateForm () {
      return await this.$refs.observer.validate()
    },
    getPayload () {
      return this.account.resources.map(r => {
        return { name: r.name, max_value: r.max_value }
      })
    }
  }
}
</script>
