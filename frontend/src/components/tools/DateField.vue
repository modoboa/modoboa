<template>
<v-menu
  v-model="menu"
  :close-on-content-click="false"
  transition="scale-transition"
  offset-y
  min-width="auto"
  >
  <template v-slot:activator="{ on, attrs }">
    <v-text-field
      :value="value"
      :label="label"
      prepend-icon="mdi-calendar"
      readonly
      v-bind="attrs"
      v-on="on"
      ></v-text-field>
  </template>
  <v-date-picker
    :value="value"
    @input="update"
    no-title
    >
  </v-date-picker>
</v-menu>
</template>

<script>
export default {
  props: ['value', 'label'],
  data () {
    return {
      menu: false
    }
  },
  methods: {
    update (value) {
      this.$emit('input', value)
      this.menu = false
    }
  }
}
</script>
