<template>
  <v-card>
    <v-card-title class="text-headline-medium">
      <span> {{ $gettext('DNS configuration for ') }} {{ domain.name }} </span>
    </v-card-title>
    <v-card-text>
      <p class="text-subtitle-1 text-grey-darken-2 mb-4">
        {{
          $gettext(
            'Here is an example of DNS configuration (bind format). Replace values between [ ] by the appropriate ones.'
          )
        }}
      </p>
      <v-alert
        class="mb-4"
        border="start"
        border-color="primary lighten-3"
        elevation="2"
        color="white"
      >
        <div class="text-headline-small">MX</div>
        <pre>
mail.{{ domain.name }}. IN A <strong>[{{$gettext('IP address of your Modoboa server')}}]</strong>
@ IN MX 10 mail.{{ domain.name }}.</pre>
      </v-alert>
      <v-alert
        class="mb-4"
        border="start"
        border-color="primary lighten-3"
        elevation="2"
        dense
        color="white"
      >
        <div class="text-headline-small">SPF</div>
        <pre>@ IN TXT "v=spf1 mx ~all"</pre>
      </v-alert>

      <v-alert
        v-if="domain.enable_dkim && domain.dkim_public_key"
        class="mb-4"
        border="start"
        border-color="primary lighten-3"
        elevation="2"
        dense
        color="white"
      >
        <div class="text-headline-small">DKIM</div>
        <DKIMKeyViewer :domain="domain" />
      </v-alert>
      <v-alert
        class="mb-4"
        border="start"
        border-color="primary lighten-3"
        elevation="2"
        dense
        color="white"
      >
        <div class="text-headline-small">DMARC</div>
        <pre>
_dmarc.{{ domain.name }}. IN TXT "v=DMARC1; p=quarantine; pct=100;"</pre
        >
      </v-alert>
      <v-alert
        class="mb-4"
        border="start"
        border-color="primary lighten-3"
        elevation="2"
        dense
        color="white"
      >
        <div class="text-headline-small">
          {{ $gettext('Auto configuration') }}
        </div>
        <pre>
autoconfig.{{ domain.name }}. IN CNAME <strong>[{{$gettext('hostname of your automx server')}}]</strong>
autodiscover.{{ domain.name }}. IN CNAME <strong>[{{$gettext('hostname of your automx server')}}]</strong></pre>
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
import DKIMKeyViewer from './DKIMKeyViewer.vue'

const emit = defineEmits(['close'])
defineProps({
  domain: { type: Object, default: null },
})
</script>

<style scoped>
pre {
  overflow-x: scroll;
}
</style>
