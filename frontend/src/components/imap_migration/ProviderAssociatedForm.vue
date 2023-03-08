<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    vid="initialdomain"
    >
    <v-text-field
      ref="initialdomainField"
      v-model="domain.initialdomain"
      :error-messages="errors"
      :placeholder="'provider.domain' | translate"
      outlined
      dense
      @input="update"
      @keydown="onKeyDown"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    vid="newd_omain"
    >
    <v-text-field
      ref="newdomainField"
      v-model="domain.new_domain"
      :error-messages="errors"
      :placeholder="'local.domain' | translate"
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
        {{domain.name}} --> {{domain.new_domain}}
      </template>
      <template v-else>
        {{domain.name}} --> {{domain.name}}
      </template>
  </v-chip>
</validation-observer>
</template>

<script>

export default {
  props: ['value'],
  data () {
    return {
      domains: [],
      domain: {
        initialdomain: '',
        new_domain: ''
      }
    }
  },
  methods: {
    async validateForm () {
      return await this.$refs.observer.validate()
    },
    update () {
      this.$emit('input', this.domains)
    },
    async addDomain () {
      if (await this.validateForm()) {
        this.domains.push({
          name: this.domain.initialdomain,
          new_domain: this.domain.new_domain
        })
        this.$emit('input', this.domains)
        this.$refs.initialdomainField.reset()
        this.$refs.newdomainField.reset()
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
