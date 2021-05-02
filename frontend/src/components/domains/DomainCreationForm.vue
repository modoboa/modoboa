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
        <domain-general-form ref="form_1" :domain="domain" />
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
        <domain-dns-form ref="form_2" :domain="domain" />
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
        <domain-limitations-form ref="form_3" :domain="domain" />
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
        <domain-options-form ref="form_4" :domain="domain" @createAdmin="updateCreateAdmin" />
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
        <creation-summary
          :sections="summarySections"
          @modify-step="val => step = val"
          />
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
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import CreationSummary from '@/components/tools/CreationSummary'
import DomainDNSForm from './DomainDNSForm'
import DomainGeneralForm from './DomainGeneralForm'
import DomainLimitationsForm from './DomainLimitationsForm'
import DomainOptionsForm from './DomainOptionsForm'

export default {
  props: ['value'],
  components: {
    ConfirmDialog,
    CreationSummary,
    'domain-dns-form': DomainDNSForm,
    DomainGeneralForm,
    DomainLimitationsForm,
    DomainOptionsForm
  },
  computed: {
    summarySections () {
      const result = [
        {
          title: this.$gettext('General'),
          items: [
            { key: this.$gettext('Name'), value: this.domain.name },
            { key: this.$gettext('Type'), value: this.domain.type },
            { key: this.$gettext('Enabled'), value: this.domain.enabled, type: 'yesno' }
          ]
        },
        {
          title: this.$gettext('DNS'),
          items: [
            { key: this.$gettext('Enable DNS checks'), value: this.domain.enable_dns_checks, type: 'yesno' },
            { key: this.$gettext('Enable DKIM signing'), value: this.domain.enable_dkim, type: 'yesno' }
          ]
        },
        {
          title: this.$gettext('Limitations'),
          items: [
            { key: this.$gettext('Quota'), value: this.domain.quota },
            { key: this.$gettext('Default mailbox quota'), value: this.domain.default_mailbox_quota },
            { key: this.$gettext('Message sending limit'), value: this.domain.message_sending_limit }
          ]
        },
        {
          title: this.$gettext('Options'),
          items: [
            { key: this.$gettext('Create a domain administrator'), value: this.createAdmin, type: 'yesno' }
          ]
        }
      ]
      if (this.domain.enable_dkim) {
        result[1].items.push({ key: this.$gettext('DKIM key selector'), value: this.domain.dkim_key_selector })
        result[1].items.push({ key: this.$gettext('DKIM key length'), value: this.domain.dkim_key_length })
      }
      if (this.createAdmin) {
        result[3].items.push({ key: this.$gettext('Administrator name'), value: this.domain.domain_admin.username })
        result[3].items.push({
          key: this.$gettext('Random password'),
          value: this.domain.domain_admin.with_random_password,
          type: 'yesno'
        })
        result[3].items.push({
          key: this.$gettext('With mailbox'),
          value: this.domain.domain_admin.with_mailbox,
          type: 'yesno'
        })
        result[3].items.push({
          key: this.$gettext('Create aliases'),
          value: this.domain.domain_admin.with_aliases,
          type: 'yesno'
        })
      }
      return result
    }
  },
  data () {
    return {
      createAdmin: false,
      domain: {
        domain_admin: {}
      },
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
      const valid = await this.$refs[`form_${current}`].$refs.observer.validate()
      if (!valid) {
        return
      }
      this.step = next
    },
    updateCreateAdmin (value) {
      this.createAdmin = value
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
