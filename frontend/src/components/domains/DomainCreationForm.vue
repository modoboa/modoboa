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
      <v-stepper-step step="5">
        <translate>Summary</translate>
      </v-stepper-step>
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mx-16 mt-4">
      <v-stepper-content step="1">
        <validation-observer ref="observer_1">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              :label="'Name' | translate"
              v-model="domain.name"
              :error-messages="errors"
              outlined
              />
          </validation-provider>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <choice-field v-model="domain.type"
                          :label="'Type' | translate"
                          :choices="domainTypes"
                          :error-messages="errors"
                          />
          </validation-provider>
          <v-switch :label="'Enabled' | translate" v-model="domain.enabled" />
        </validation-observer>
        <div class="d-flex justify-center">
          <v-btn
            color="primary"
            @click="goToNextStep(1, 2)"
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
          :disabled="!domain.enable_dkim"
          outlined
          />
        <choice-field
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
      <v-stepper-content step="3">
        <validation-observer ref="observer_3">
          <v-text-field
            :label="'Quota' | translate"
            :hint="'Quota shared between mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
            persistent-hint
            v-model="domain.quota"
            :error-messages="errors"
            outlined
            />
          <v-text-field
            :label="'Default mailbox quota' | translate"
            :hint="'Default quota applied to mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
            persistent-hint
            v-model="domain.default_mailbox_quota"
            :error-messages="errors"
            outlined
            />
          <validation-provider
            v-slot="{ errors }"
            rules="number"
            >
            <v-text-field
              :label="'Message sending limit' | translate"
              :hint="'Number of messages this domain can send per day.' | translate"
              persistent-hint
              v-model="domain.message_sending_limit"
              :error-messages="errors"
              outlined
              />
          </validation-provider>
        </validation-observer>
        <div class="d-flex justify-center mt-8">
          <v-btn @click="step = 2" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(3, 4)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="4">
        <validation-observer ref="observer_4">
          <v-switch v-model="createAdmin"
                    :label="'Create a domain administrator' | translate"
                    />
          <v-text-field
            :label="'Name' | translate"
            :hint="'Name of the administrator' | translate"
            persistent-hint
            v-model="domain.dom_admin_username"
            :error-messages="errors"
            outlined
            :disabled="!createAdmin"
            />
          <v-switch v-model="domain.dom_admin_random_password"
                    :label="'Random password' | translate"
                    :disabled="!createAdmin"
                    :hint="'Generate a random password for the administrator.' | translate"
                    persistent-hint
                    />
          <v-switch v-model="domain.dom_admin_with_mailbox"
                    :label="'With a mailbox' | translate"
                    :disabled="!createAdmin"
                    :hint="'Create a mailbox for the administrator.' | translate"
                    persistent-hint
                    />
          <v-switch v-model="domain.dom_admin_create_aliases"
                    :label="'Create aliases' | translate"
                    :disabled="!createAdmin"
                    :hint="'Create standard aliases for the domain.' | translate"
                    persistent-hint
                    />

        </validation-observer>
        <div class="d-flex justify-center mt-8">
          <v-btn @click="step = 3" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(4, 5)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="5">
        <div class="text-center text-h3"><translate>Summary</translate></div>
        <div class="subtitle text-subtitle-1 mt-4">
          <translate>General</translate>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Name</translate></v-col>
          <v-col class="text-right">{{ domain.name }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Type</translate></v-col>
          <v-col class="text-right">{{ domain.type }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Enabled</translate></v-col>
          <v-col class="text-right">{{ domain.enabled }}</v-col>
        </v-row>
        <div class="subtitle text-subtitle-1 mt-4">
          <translate>DNS</translate>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Enable DNS checks</translate></v-col>
          <v-col class="text-right">{{ domain.enable_dns_checks }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Enable DKIM signing</translate></v-col>
          <v-col class="text-right">{{ domain.enable_dkim }}</v-col>
        </v-row>
        <v-row dense v-if="domain.enable_dkim">
          <v-col><translate class="grey--text">DKIM key selector</translate></v-col>
          <v-col class="text-right">{{ domain.dkim_key_selector }}</v-col>
        </v-row>
        <v-row dense v-if="domain.enable_dkim">
          <v-col><translate class="grey--text">DKIM key length</translate></v-col>
          <v-col class="text-right">{{ domain.dkim_key_length }}</v-col>
        </v-row>
        <div class="subtitle text-subtitle-1 mt-4">
          <translate>Limitations</translate>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Quota</translate></v-col>
          <v-col class="text-right">{{ domain.quota }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Default mailbox quota</translate></v-col>
          <v-col class="text-right">{{ domain.default_mailbox_quota }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Message sending limit</translate></v-col>
          <v-col class="text-right">{{ domain.message_sending_limit }}</v-col>
        </v-row>
        <div class="subtitle text-subtitle-1 mt-4">
          <translate>Options</translate>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Create a domain administrator</translate></v-col>
          <v-col class="text-right">{{ createAdmin }}</v-col>
        </v-row>
        <div v-if="createAdmin">
          <v-row dense>
            <v-col><translate class="grey--text">Administrator name</translate></v-col>
            <v-col class="text-right">{{ domain.dom_admin_username }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">Random password</translate></v-col>
            <v-col class="text-right">{{ domain.dom_admin_random_password }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">With mailbox</translate></v-col>
            <v-col class="text-right">{{ domain.dom_admin_with_mailbox }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">Create aliases</translate></v-col>
            <v-col class="text-right">{{ domain.dom_admin_create_aliases }}</v-col>
          </v-row>
        </div>
        <div class="d-flex justify-center mt-8">
          <v-btn
            color="primary"
            @click="submit"
            large
            >
            <translate>Confirm and create</translate>
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
      createAdmin: false,
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
  mounted () {
    this.initDomain()
  },
  methods: {
    initDomain () {
      this.domain = {
        type: 'domain',
        enabled: true,
        enable_dns_checks: true,
        enable_dkim: false,
        dkim_key_selector: 'modoboa',
        quota: 0,
        default_mailbox_quota: 0,
        dom_admin_username: 'admin',
        dom_admin_random_password: false,
        dom_admin_with_mailbox: false,
        dom_admin_create_aliases: false
      }
    },
    close () {
      this.$emit('close')
      this.initDomain()
      this.step = 1
    },
    async goToNextStep (current, next) {
      const valid = await this.$refs[`observer_${current}`].validate()
      if (!valid) {
        return
      }
      this.step = next
    },
    submit () {
      this.$store.dispatch('domains/createDomain', this.domain).then(resp => {
        this.close()
      })
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
  width: 70%;
}
.subtitle {
  color: #000;
  border-bottom: 1px solid #DBDDDF;
}
</style>
