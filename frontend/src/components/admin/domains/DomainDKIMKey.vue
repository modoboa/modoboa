<template>
  <v-card>
    <v-card-title>
      <span class="headline">
        {{ $gettext('DKIM public key for') }} {{ domain.name }}
      </span>
    </v-card-title>
    <v-card-text>
      <p>{{ $gettext('Raw format. Click to copy') }}</p>
      <v-alert
        border="start"
        colored-border
        border-color="primary lighten-3"
        elevation="2"
        dense
      >
        <button class="dkimbutton" @click="copyPubDKIM()">
          <pre id="dkimpub" class="dkim">{{ domain.dkim_public_key }}</pre>
        </button>
      </v-alert>
    </v-card-text>
    <v-card-text>
      <p>{{ $gettext('Bind/named format. Click to copy') }}</p>
      <v-alert
        border="start"
        colored-border
        border-color="primary lighten-3"
        elevation="2"
        dense
      >
        <DKIMKeyViewer :domain="domain" />
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="emit('close')">
        {{ $gettext('Close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="js">
import { useGettext } from 'vue3-gettext'
import DKIMKeyViewer from './DKIMKeyViewer.vue'

const { $gettext } = useGettext()

defineProps({
  domain: { type: Object, default: null },
})
const emit = defineEmits(['close'])

function copyPubDKIM() {
  navigator.clipboard.writeText(document.getElementById('dkimpub').textContent)
}
</script>

<style>
.dkimbutton {
  border-radius: 10px;
}
.dkimbutton:hover {
  background-color: rgba(131, 131, 250, 0.283);
  transition: all 0.8s;
}
.dkimbutton:active {
  background-color: rgba(60, 255, 60, 0.136);
  transition: all 0.2s;
}
.dkim {
  white-space: normal;
  word-break: break-all;
}
</style>
