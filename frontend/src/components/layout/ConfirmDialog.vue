<template>
<v-dialog v-model="dialog" max-width="290">
  <v-card>
    <v-card-title class="headline">
      {{ message }}
    </v-card-title>
    <v-card-actions>
      <v-spacer></v-spacer>

      <v-btn
        text
        @click="cancel"
        >
        <translate>No</translate>
      </v-btn>
      <v-btn
        color="primary"
        text
        @click="confirm"
        >
        <translate>Yes</translate>
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
</template>

<script>
export default {
  props: ['value', 'message'],
  computed: {
    dialog: {
      get () {
        return this.value
      },
      set (newValue) {
        this.$emit('input', newValue)
      }
    }
  },
  methods: {
    confirm () {
      this.$emit('confirm')
      this.dialog = false
    },
    cancel () {
      this.dialog = false
    }
  }
}
</script>
