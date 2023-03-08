<template>
<creation-form
  :title="'New provider'|translate"
  :steps="steps"
  :form-observer-getter="getObserver"
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
    formatAssociatedDomains () {
      let associatedDomains = ''
      for (const domain of this.provider.domains) {
        associatedDomains += `${domain.name} => ${domain.new_domain}, `
      }
      return associatedDomains
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
          items: [
            { key: this.$gettext('Perform a connection check'), value: this.formatAssociatedDomains }
          ]
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
      this.$emit('close')
    },
    getObserver (step) {
      return this.$refs[`form_${step}`].$refs.observer
    },
    validateProvider () {

    },
    performConnectionCheck () {

    },
    submit () {
      const data = JSON.parse(JSON.stringify(this.provider))
      console.log(this.provider)
      this.$store.dispatch('providers/createProvider', data).then(resp => {
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
