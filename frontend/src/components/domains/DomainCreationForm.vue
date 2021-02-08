<template>
<div class="d-flex justify-center inner">
  <v-stepper v-model="step">
    <v-stepper-header class="align-center px-10">
      <v-img
        src="../../assets/Modoboa_RVB-BLEU-SANS.png"
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
      <v-stepper-step :complete="step > 4" step="4">
        <translate>Options</translate>
      </v-stepper-step>
      <v-stepper-step step="5">
        <translate>Summary</translate>
      </v-stepper-step>
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mt-4 d-flex justify-center">
      <v-stepper-content step="1" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New domain</translate> /
          <translate>General</translate>
        </div>
        <validation-observer ref="observer_1">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              :label="'Domain name (ex: domain.tld)' | translate"
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
          <v-switch
            :label="'Enabled' | translate"
            v-model="domain.enabled"
            :hint="'Control if this domain will be allowed to send and receive messages' | translate"
            persistent-hint
            />
        </validation-observer>
        <div class="d-flex justify-end">
          <v-btn
            color="primary"
            @click="goToNextStep(1, 2)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="2" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New domain</translate> /
          <translate>DNS</translate>
        </div>
        <v-switch
          :label="'Enable DNS checks' | translate"
          v-model="domain.enable_dns_checks"
          />
        <v-switch
          :label="'Enable DKIM signing' | translate"
          v-model="domain.enable_dkim"
          />
        <v-text-field
          :label="'DKIM key selector' | translate"
          v-model="domain.dkim_key_selector"
          :disabled="!domain.enable_dkim"
          outlined
          />
        <choice-field
          v-model="domain.dkim_key_length"
          :label="'DKIM key length' | translate"
          :choices="dkimKeyLengths"
          :disabled="!domain.enable_dkim"
          />
        <div class="d-flex justify-end mt-8">
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
      <v-stepper-content step="3" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New domain</translate> /
          <translate>Limitations</translate>
        </div>
        <validation-observer ref="observer_3">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              :label="'Quota' | translate"
              :hint="'Quota shared between mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
              persistent-hint
              v-model="domain.quota"
              :error-messages="errors"
              class="mb-4"
              outlined
              />
          </validation-provider>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              :label="'Default mailbox quota' | translate"
              :hint="'Default quota applied to mailboxes. Can be expressed in KB, MB (default) or GB. A value of 0 means no quota.' | translate"
              persistent-hint
              v-model="domain.default_mailbox_quota"
              :error-messages="errors"
              class="mb-4"
              outlined
              />
          </validation-provider>
          <validation-provider
            v-slot="{ errors }"
            rules="numeric"
            >
            <v-text-field
              :label="'Message sending limit' | translate"
              :hint="'Number of messages this domain can send per day. Leave empty for no limit.' | translate"
              persistent-hint
              v-model="domain.message_sending_limit"
              :error-messages="errors"
              outlined
              />
          </validation-provider>
        </validation-observer>
        <div class="d-flex justify-end mt-8">
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
      <v-stepper-content step="4" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New domain</translate> /
          <translate>Options</translate>
        </div>
        <validation-observer ref="observer_4">
          <v-switch v-model="createAdmin"
                    :label="'Create a domain administrator' | translate"
                    />
          <validation-provider
            v-slot="{ errors }"
            :rules="(createAdmin) ? 'required' : ''"
            >
            <v-text-field
              :label="'Name' | translate"
              :hint="'Name of the administrator' | translate"
              persistent-hint
              v-model="domain.domain_admin.username"
              :error-messages="errors"
              outlined
              :disabled="!createAdmin"
              :suffix="`@${domain.name}`"
              />
          </validation-provider>
          <v-switch v-model="domain.domain_admin.with_random_password"
                    :label="'Random password' | translate"
                    :disabled="!createAdmin"
                    :hint="'Generate a random password for the administrator.' | translate"
                    persistent-hint
                    />
          <v-switch v-model="domain.domain_admin.with_mailbox"
                    :label="'With a mailbox' | translate"
                    :disabled="!createAdmin"
                    :hint="'Create a mailbox for the administrator.' | translate"
                    persistent-hint
                    />
          <v-switch v-model="domain.domain_admin.with_aliases"
                    :label="'Create aliases' | translate"
                    :disabled="!createAdmin"
                    :hint="'Create standard aliases for the domain.' | translate"
                    persistent-hint
                    />

        </validation-observer>
        <div class="d-flex justify-end mt-8">
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
      <v-stepper-content step="5" class="flex-grow-0">
        <div class="text-center text-h3"><translate>Summary</translate></div>
        <div class="subtitle mt-4 d-flex">
          <translate class="text-h6">General</translate>
          <a href="#" class="edit-link ml-auto" @click="step = 1"><translate>Modify</translate></a>
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
          <v-col class="text-right">{{ domain.enabled|yesno }}</v-col>
        </v-row>
        <div class="subtitle mt-4 d-flex">
          <translate class="text-h6">DNS</translate>
          <a href="#" class="edit-link ml-auto" @click="step = 2"><translate>Modify</translate></a>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Enable DNS checks</translate></v-col>
          <v-col class="text-right">{{ domain.enable_dns_checks|yesno }}</v-col>
        </v-row>
        <v-row dense>
          <v-col><translate class="grey--text">Enable DKIM signing</translate></v-col>
          <v-col class="text-right">{{ domain.enable_dkim|yesno }}</v-col>
        </v-row>
        <v-row dense v-if="domain.enable_dkim">
          <v-col><translate class="grey--text">DKIM key selector</translate></v-col>
          <v-col class="text-right">{{ domain.dkim_key_selector }}</v-col>
        </v-row>
        <v-row dense v-if="domain.enable_dkim">
          <v-col><translate class="grey--text">DKIM key length</translate></v-col>
          <v-col class="text-right">{{ domain.dkim_key_length }}</v-col>
        </v-row>
        <div class="subtitle mt-4 d-flex">
          <translate class="text-h6">Limitations</translate>
          <a href="#" class="edit-link ml-auto" @click="step = 3"><translate>Modify</translate></a>
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
        <div class="subtitle mt-4 d-flex">
          <translate class="text-h6">Options</translate>
          <a href="#" class="edit-link ml-auto" @click="step = 4"><translate>Modify</translate></a>
        </div>
        <v-row dense>
          <v-col><translate class="grey--text">Create a domain administrator</translate></v-col>
          <v-col class="text-right">{{ createAdmin|yesno }}</v-col>
        </v-row>
        <div v-if="createAdmin">
          <v-row dense>
            <v-col><translate class="grey--text">Administrator name</translate></v-col>
            <v-col class="text-right">{{ domain.domain_admin.username }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">Random password</translate></v-col>
            <v-col class="text-right">{{ domain.domain_admin.with_random_password|yesno }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">With mailbox</translate></v-col>
            <v-col class="text-right">{{ domain.domain_admin.with_mailbox|yesno }}</v-col>
          </v-row>
          <v-row dense>
            <v-col><translate class="grey--text">Create aliases</translate></v-col>
            <v-col class="text-right">{{ domain.domain_admin.with_aliases|yesno }}</v-col>
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
  <confirm-dialog ref="confirm" />
</div>
</template>

<script>
import { bus } from '@/main'
import ChoiceField from '@/components/tools/ChoiceField'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  props: ['value'],
  components: {
    ChoiceField,
    ConfirmDialog
  },
  data () {
    return {
      createAdmin: false,
      domain: {
        domain_admin: {}
      },
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
        name: '',
        type: 'domain',
        enabled: true,
        enable_dns_checks: true,
        enable_dkim: false,
        dkim_key_selector: 'modoboa',
        quota: 0,
        default_mailbox_quota: 0,
        domain_admin: {
          username: 'admin',
          with_random_password: false,
          with_mailbox: false,
          with_aliases: false
        }
      }
    },
    async close (withConfirm) {
      if (withConfirm) {
        const confirm = await this.$refs.confirm.open(
          this.$gettext('Warning'),
          this.$gettext('If you close this form now, your modifications won\'t be saved. Do you confirm?'),
          {
            color: 'error'
          }
        )
        if (!confirm) {
          return
        }
      }
      this.$emit('close')
      this.initDomain()
      this.step = 1
      this.$refs.observer_1.reset()
      this.$refs.observer_3.reset()
      this.$refs.observer_4.reset()
    },
    async goToNextStep (current, next) {
      const valid = await this.$refs[`observer_${current}`].validate()
      if (!valid) {
        return
      }
      this.step = next
    },
    submit () {
      const data = JSON.parse(JSON.stringify(this.domain))
      if (!this.createAdmin) {
        delete data.domain_admin
      }
      this.$store.dispatch('domains/createDomain', data).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Domain created') })
        this.close()
      })
    }
  }
}
</script>

<style lang="scss">
.inner {
  background-color: #fff;
}
.v-stepper {
  width: 100%;
  overflow: auto;

  &__content {
    width: 60%;
  }

  &__items {
    overflow-y: auto;
  }

  &__wrapper {
    padding: 0 10px;
  }
}
.subtitle {
  color: #000;
  border-bottom: 1px solid #DBDDDF;
}

.edit-link {
  text-decoration: none;
}
</style>
