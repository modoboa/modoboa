<template>
<creation-form
  ref="form"
  :title="'New provider'|translate"
  :steps="steps"
  :form-observer-getter="getObserver"
  :form-getter="getForm"
  :validate-object="validateProvider"
  :summary-sections="summarySections"
  @close="close"
  @create="submit"
  >
  <template v-slot:form.general="{ step }">
    <provider-general-form :ref="`form_${step}`" v-model="provider" />
  </template>
  <template v-slot:form.associated="{ step }">
    <provider-associated-form :ref="`form_${step}`" v-model="provider.domains" />
  </template>
</creation-form>
</template>

<script>
import { bus } from '@/main'
import CreationForm from '@/components/tools/CreationForm'
import ProviderAssociatedForm from './ProviderAssociatedForm'
import ProviderGeneralForm from './ProviderGeneralForm'

export default {
  props: ['value'],
  components: {
    CreationForm,
    'provider-associated-form': ProviderAssociatedForm,
    ProviderGeneralForm
  },
  computed: {
    associatedDomainsSummary () {
      const result = []
      for (const domain of this.provider.domains) {
        const value = domain.new_domain ? `${domain.name} => ${domain.new_domain.name}` : domain.name
        result.push(
          { key: '', value }
        )
      }
      return result
    },
    summarySections () {
      const result = [
        {
          title: this.$gettext('General'),
          items: [
            { key: this.$gettext('Name'), value: this.provider.name },
            { key: this.$gettext('Address'), value: this.provider.address },
            { key: this.$gettext('Port'), value: this.provider.port },
            { key: this.$gettext('Secured'), value: this.provider.secured, type: 'yesno' }
          ]
        },
        {
          title: this.$gettext('Associated domains'),
          items: this.associatedDomainsSummary
        }
      ]
      return result
    },
    steps () {
      return [
        { name: 'general', title: this.$gettext('General') },
        { name: 'associated', title: this.$gettext('Associated domains') }
      ]
    }
  },
  data () {
    return {
      provider: {
        domains: []
      },
      formErrors: {}
    }
  },
  mounted () {
    this.initProvider()
  },
  methods: {
    initProvider () {
      this.provider = {
        name: '',
        address: '',
        port: 993,
        secured: true,
        domains: []
      }
    },
    close () {
      this.initProvider()
      this.$refs.form.resetForm()
      this.$emit('close')
    },
    getForm (step) {
      return this.$refs[`form_${step}`]
    },
    getObserver (step) {
      return this.$refs[`form_${step}`].$refs.observer
    },
    validateProvider () {

    },
    submit () {
      const data = { ...this.provider }
      data.domains = []
      for (const domain of this.provider.domains) {
        if (domain.new_domain) {
          data.domains.push({
            name: domain.name,
            new_domain: domain.new_domain.pk
          })
        } else {
          data.domains.push(domain)
        }
      }
      this.$store.dispatch('providers/createProvider', data).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Provider created') })
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
