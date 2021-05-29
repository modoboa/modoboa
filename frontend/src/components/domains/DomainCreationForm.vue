<template>
<creation-form
  :title="'New domain'|translate"
  :steps="steps"
  :form-observer-getter="getObserver"
  :validate-object="validateDomain"
  :summary-sections="summarySections"
  @close="close"
  @create="submit"
  >
  <template v-slot:form.general="{ step }">
    <domain-general-form :ref="`form_${step}`" :domain="domain" />
  </template>
  <template v-slot:form.dns="{ step }">
    <domain-dns-form :ref="`form_${step}`" :domain="domain" />
  </template>
  <template v-slot:form.limitations="{ step }">
    <domain-limitations-form :ref="`form_${step}`" :domain="domain" />
  </template>
  <template v-slot:form.options="{ step }">
    <domain-options-form :ref="`form_${step}`" :domain="domain" @createAdmin="updateCreateAdmin" />
  </template>
  <template v-slot:item.with_random_password="{ item }">
    <template v-if="item.value">
      <v-col cols="12" class="highligth white--text">
        <v-row>
          <v-col><span>{{ item.key }}</span></v-col>
          <v-col class="text-right">{{ item.value|yesno }}</v-col>
        </v-row>
        <v-row>
          <v-col class="text-right py-1">
            {{ domain.domain_admin.password }}
            <v-btn icon color="white" :title="'Copy to clipboard'|translate" @click="copyPassword">
              <v-icon>mdi-clipboard-multiple-outline</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-col>
    </template>
    <template v-else>
      <v-col><span class="grey--text">{{ item.key }}</span></v-col>
      <v-col class="text-right">{{ item.value|yesno }}</v-col>
    </template>
  </template>
</creation-form>
</template>

<script>
import { bus } from '@/main'
import CreationForm from '@/components/tools/CreationForm'
import DomainDNSForm from './DomainDNSForm'
import DomainGeneralForm from './DomainGeneralForm'
import DomainLimitationsForm from './DomainLimitationsForm'
import DomainOptionsForm from './DomainOptionsForm'

export default {
  props: ['value'],
  components: {
    CreationForm,
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
          name: 'with_random_password',
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
      steps: [
        { name: 'general', title: this.$gettext('General') },
        { name: 'dns', title: this.$gettext('DNS') },
        { name: 'limitations', title: this.$gettext('Limitations') },
        { name: 'options', title: this.$gettext('Options') }
      ]
    }
  },
  mounted () {
    this.initDomain()
  },
  methods: {
    copyPassword () {
      navigator.clipboard.writeText(this.domain.domain_admin.password).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Password copied to clipboard') })
      })
    },
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
    close () {
      this.initDomain()
      this.$emit('close')
    },
    getObserver (step) {
      return this.$refs[`form_${step}`].$refs.observer
    },
    validateDomain () {

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
        this.$router.push({ name: 'DomainDetail', params: { id: resp.data.pk } })
        bus.$emit('notification', { msg: this.$gettext('Domain created') })
        this.close()
      })
    }
  }
}
</script>

<style lang="scss">
.highligth {
  background-color: #515D78;
}
</style>
