<template>
<v-card>
  <v-card-title>
    <span class="headline">
      <translate>DNS configuration for </translate> {{ domain.name }}
    </span>
  </v-card-title>
  <v-card-text>
    <p>Here is an example of DNS configuration (bind format). Replace values between [ ] by the appropriate ones.</p>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <div class="title">MX</div>
      <pre>
mail.{{ domain.name }}. IN A <strong>[<translate>IP address of your Modoboa server</translate>]</strong>
@ IN MX 10 mail.{{ domain.name }}.</pre>
    </v-alert>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <div class="title">SPF</div>
      <pre>
@ IN TXT "v=spf1 mx ~all"</pre>
    </v-alert>

    <v-alert
      v-if="domain.enable_dkim && domain.dkim_public_key"
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <div class="title">DKIM</div>
      <pre>
{{ domain.dkim_key_selector }}._domain_key.{{ domain.name }}. IN TXT (
  {{ splitKey(`v=DKIM1;k=rsa;p=${domain.dkim_public_key}`) }}</pre>
    </v-alert>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <div class="title">DMARC</div>
      <pre>
_dmarc.{{ domain.name }}. IN TXT "v=DMARC1; p=quarantine; pct=100;"</pre>
    </v-alert>
    <v-alert
      border="left"
      colored-border
      color="primary lighten-3"
      elevation="2"
      dense
      >
      <div class="title">Auto configuration</div>
      <pre>
autoconfig.{{ domain.name }}. IN CNAME <strong>[<translate>hostname of your automx server</translate>]</strong>
autodiscover.{{ domain.name }}. IN CNAME <strong>[<translate>hostname of your automx server</translate>]</strong></pre>
    </v-alert>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn color="grey darken-1" text @click="close">
      <translate>Close</translate>
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
export default {
  props: ['domain'],
  methods: {
    close () {
      this.$emit('close')
    },
    splitKey (value) {
      let key = value
      const result = []
      while (key.length > 0) {
        if (key.length > 74) {
          result.push(`  "${key.substring(0, 74)}"`)
          key = key.substring(74)
        } else {
          result.push(`  "${key}"`)
        }
      }
      return result.join('\n')
    }
  }
}
</script>
