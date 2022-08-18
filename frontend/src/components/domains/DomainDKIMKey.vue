<style>
.v-alert {
  word-break: break-all;
}
.dkimbutton {
  border-radius: 10px;
}
.dkimbutton:hover {
    background-color: rgba(131, 131, 250, 0.283);
    transition: all 0.8s
}
.dkimbutton:active {
    background-color: rgba(60, 255, 60, 0.136);
    transition: all 0.2s
}
.dkim {
  word-break: break-all;
  overflow-wrap: anywhere;
}
</style>

<template>
<v-card>
  <v-card-title>
    <span class="headline">
      <translate>DKIM public key for </translate> {{ domain.name }}
    </span>
  </v-card-title>
  <v-card-text>
    <p><translate>Raw format. Click to copy</translate></p>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <button @click="copyPubKeyToClipboard()" class='dkimbutton'><p id='dkimpub' class='dkim'>{{ domain.dkim_public_key }}</p></button>
    </v-alert>
  </v-card-text>
  <v-card-text>
    <p><translate>Bind/named format. Click to copy</translate></p>
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
    },
    copyPubKeyToClipboard () {
      const text = document.getElementById('dkimpub').textContent
      navigator.clipboard.writeText(text)
    }
  }
}
</script>
