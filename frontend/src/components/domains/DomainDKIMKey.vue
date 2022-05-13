<template>
<v-card>
  <v-card-title>
    <span class="headline">
      <translate>DKIM public key for </translate> {{ domain.name }}
    </span>
  </v-card-title>
  <v-card-text>
    <p><translate>Raw format</translate></p>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      {{ domain.dkim_public_key }}
    </v-alert>
  </v-card-text>
  <v-card-text>
    <p><translate>Bind/named format</translate></p>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <dkim-key-viewer :domain="domain" />
    </v-alert>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn @click="close">
      <translate>Close</translate>
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import DKIMKeyViewer from './DKIMKeyViewer'

export default {
  props: {
    domain: Object
  },
  components: {
    'dkim-key-viewer': DKIMKeyViewer
  },
  methods: {
    close () {
      this.$emit('close')
    }
  }
}
</script>
