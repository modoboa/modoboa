<template>
<v-card>
  <v-card-title>
    <translate class="headline">Resources usage</translate>
  </v-card-title>
  <v-card-text>
    <div
      v-for="resource in account.resources"
      :key="resource.name"
      class="mt-4"
      >
      {{ resource.label }} ({{ Math.ceil(resource.usage) }}%)
      <v-progress-linear
        :value="resource.usage"
        :color="getProgressColor(resource.usage)"
        />
    </div>
  </v-card-text>
</v-card>
</template>

<script>
export default {
  props: {
    account: Object
  },
  methods: {
    getProgressColor (value) {
      if (value < 50) {
        return 'primary'
      }
      if (value < 80) {
        return 'warning'
      }
      return 'error'
    }
  }
}
</script>
