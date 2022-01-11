<template>
<v-card>
  <v-card-title>
    <span class="headline"><translate>New recovery codes</translate></span>
  </v-card-title>
  <v-card-text>
    <v-alert type="info">
      <translate>
        The following recovery codes can be used one time each to let
        you regain access to your account, in case you lose your phone
        for example. Make sure to save them in a safe place, otherwise
        you won't be able to access your account anymore.
      </translate>
    </v-alert>
    <ul>
      <li v-for="token in tokens" :key="token">
        {{ token }}
      </li>
    </ul>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      color="grey darken-1"
      text
      @click="close"
      >
      <translate>Close</translate>
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
export default {
  props: {
    tokens: Array
  },
  methods: {
    close () {
      this.$emit('close')
    }
  }
}
</script>
