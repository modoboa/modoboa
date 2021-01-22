<template>
<div class="d-flex justify-center inner">
  <v-stepper v-model="step">
    <v-stepper-header class=" align-center">
      <v-img
        src="../../assets/Modoboa_RVB-ORANGE-SANS.png"
        max-width="190"
        />
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
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mx-14 mt-4">
      <v-stepper-content step="1">
        <v-text-field
          :label="'Name' | translate"
          v-model="domain.name"
          outlined
          :error="formErrors['name'] !== undefined"
          :error-messages="formErrors['name']"
          />
        <choice-field v-model="domain.type" :label="'Type' | translate" :choices="domainTypes" />
        <v-switch :label="'Enabled' | translate" v-model="domain.enabled" />
        <div class="d-flex justify-center">
          <v-btn
            color="primary"
            @click="step = 2"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="2">
        <v-switch
          label="Enable DNS checks"
          v-model="domain.enable_dns_checks"
          />
        <v-switch
          label="Enable DKIM signing"
          v-model="domain.enable_dkim"
          />
        <v-text-field
          label="DKIM key selector"
          v-model="domain.dkim_key_selector"
          v-if="domain.enable_dkim"
          outlined
          />
        <choice-field
          v-if="domain.enable_dkim"
          v-model="domain.dkim_key_length"
          :label="'DKIM key length' | translate"
          :choices="dkimKeyLengths"
          />
        <div class="d-flex justify-center mt-8">
          <v-btn @click="step = 1" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="step = 3"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</div>
</template>

<script>
import ChoiceField from '@/components/tools/ChoiceField'
export default {
  props: ['value'],
  components: {
    ChoiceField
  },
  data () {
    return {
      domain: {},
      domainTypes: [
        {
          label: 'Domain',
          icon: 'mdi-earth',
          value: 'domain'
        },
        {
          label: 'Relay domain',
          icon: 'mdi-earth',
          value: 'relaydomain'
        }
      ],
      dkimKeyLengths: [
        {
          label: '1024',
          value: 1024
        },
        {
          label: '2048',
          value: 2048
        },
        {
          label: '4096',
          value: 4096
        }
      ],
      formErrors: {},
      step: 1
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.step = 1
    },
    selectType (value) {
      this.$set(this.domain, 'type', value)
    }
  }
}
</script>

<style lang="scss" scoped>
.inner {
  height: 100%;
  background-color: #fff;
}
.v-stepper {
  height: 100%;
  width: 60%;
}
</style>
