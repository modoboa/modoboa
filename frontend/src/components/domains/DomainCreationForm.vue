<template>
<v-dialog v-model="dialog" max-width="600">
  <v-stepper v-model="step">
    <v-stepper-header>
      <v-stepper-step :complete="step > 1" step="1">
        <translate>General</translate>
      </v-stepper-step>
      <v-stepper-step :complete="step > 2" step="2">
        <translate>DNS</translate>
      </v-stepper-step>
      <v-stepper-step :complete="step > 3" step="3">
        <translate>Limitations</translate>
      </v-stepper-step>
      <v-stepper-step step="4">
        <translate>Options</translate>
      </v-stepper-step>
    </v-stepper-header>
    <v-stepper-items>
      <v-stepper-content step="1">
        <v-text-field
          :label="'Name' | translate"
          v-model="domain.name"
          :error="formErrors['name'] !== undefined"
          :error-messages="formErrors['name']"
          />
        <v-select :label="'Type' | translate" :items="domainTypes" />
        <v-checkbox :label="'Enabled' | translate" v-model="domain.enabled" />
        <div class="float-right">
          <v-btn text @click="close">
            <translate>Cancel</translate>
          </v-btn>
          <v-btn
            text
            color="primary"
            @click="step = 2"
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="2">
        <v-checkbox
          label="Enable DNS checks"
          v-model="domain.enable_dns_checks"
          />
        <v-checkbox
          label="Enable DKIM signing"
          v-model="domain.enable_dkim"
          />
        <v-text-field
          label="DKIM key selector"
          v-model="domain.dkim_key_selector"
          v-if="domain.enable_dkim"
          />
        <v-text-field
          label="DKIM key length"
          v-model="domain.dkim_key_length"
          v-if="domain.enable_dkim"
          />

        <div class="float-right">
          <v-btn text @click="dialog = false">
            <translate>Cancel</translate>
          </v-btn>
          <v-btn
            text
            color="primary"
            @click="step = 3"
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</v-dialog>
</template>

<script>
export default {
  props: ['value'],
  components: {
  },
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
  data () {
    return {
      domain: {},
      domainTypes: ['Domain', 'Relay domain'],
      formErrors: {},
      step: 1
    }
  },
  methods: {
    close () {
      this.dialog = false
      this.step = 1
    }
  }
}
</script>
