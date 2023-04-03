<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules=""
    vid="name"
    >
    <v-text-field
      ref="initialdomainField"
      v-model="domain.name"
      :error-messages="errors"
      :placeholder="'Name of the domain to migrate' | translate"
      outlined
      dense
      @input="update"
      @keydown="onKeyDown"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules=""
    vid="new_domain"
    >
    <v-autocomplete
      v-model="domain.new_domain"
      :error-messages="errors"
      :label="'Local domain (optional)'|translate"
      :items="localDomains"
      item-text="name"
      return-object
      outlined
      dense
      @input="update"
      @keydown="onKeyDown"
      />
  </validation-provider>
  <v-btn
    color="primary"
    @click="addDomain"
    >
    <v-icon>mdi-plus</v-icon>
  </v-btn>
  <v-spacer />
  <v-chip
    v-for="(domain, index) in domains"
    :key="index"
    class="mr-2 mt-2"
    close
    @click:close="removeDomain(index)"
    >
     <template v-if="domain.new_domain">
        {{domain.name}} --> {{domain.new_domain.name}}
      </template>
      <template v-else>
        {{domain.name}}
      </template>
  </v-chip>
</validation-observer>
</template>

<script>
import domainsApi from '@/api/domains'
import providerApi from '@/api/imap_migration/providers'

export default {
  props: ['value'],
  data () {
    return {
      domains: [],
      domain: {
        name: '',
        new_domain: ''
      },
      localDomains: []
    }
  },
  methods: {
    reset () {
      this.domains = []
      this.domain = {
        name: '',
        new_domain: ''
      }
    },
    async validateForm () {
      return await this.$refs.observer.validate()
    },
    update () {
      this.$emit('input', this.domains)
    },
    async addDomain () {
      if (await this.validateForm()) {
        providerApi.checkAssociatedDomain(this.domain).then(response => {
          if (response.status === 200) {
            this.domains.push({
              name: this.domain.name,
              new_domain: this.domain.new_domain
            })
            this.$refs.observer.reset()
            this.domain = {
              name: '',
              new_domain: ''
            }
            this.$emit('input', this.domains)
          }
        }).catch(error => {
          this.$refs.observer.setErrors(error.response.data)
        })
      }
    },
    removeDomain (index) {
      this.domains.splice(index, 1)
      this.$emit('input', this.domains)
    },
    onKeyDown (e) {
      const keyCode = e.keyCode
      if (keyCode === 13 || keyCode === 9) {
        // on enter or tab
        this.addDomain()
        e.preventDefault()
      }
    }
  },
  mounted () {
    domainsApi.getDomains().then(resp => {
      this.localDomains = resp.data
    })
  },
  watch: {
    value: {
      handler: function (newValue) {
        if (newValue) {
          this.domains = [...newValue]
        } else {
          this.domains = []
        }
      },
      immediate: true
    }
  }
}

</script>
