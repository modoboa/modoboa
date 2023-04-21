<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      :label="'Provider name' | translate"
      v-model="form.name"
      :error-messages="errors"
      outlined
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
      >
      <v-text-field
      :label="'Address (hostname or IP)' | translate"
      v-model="form.address"
      :error-messages="errors"
      outlined
      @input="update"
      />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required|portNumber"
      >
      <v-text-field
      :label="'IMAP Port' | translate"
      v-model="form.port"
      type="number"
      :error-messages="errors"
      outlined
      @input="update"
      />
  </validation-provider>
  <v-switch
    :label="'Secured' | translate"
    v-model="form.secured"
    :hint="'Is the IMAP connection secured using SSL/TLS or StartTLS' | translate"
    persistent-hint
    @change="update"
    />
  <div class="my-7">
    <v-btn
      :loading="loading"
      color="primary"
      @click="checkConnection"
      >
      <translate>Check connection: </translate>
      <v-icon
        v-if="connectionStatus === 0"
        color="blue-grey-darken-2"
        >
        mdi-help-circle-outline
      </v-icon>
      <v-icon
        v-else-if="connectionStatus === 1"
        color="success"
        >
        mdi-check-all
      </v-icon>
      <v-icon
        v-else
        color="warning"
        >
        mdi-alert-circle-outline
      </v-icon>
      <template v-slot:loader>
        <span class="custom-loader">
          <v-icon light>mdi-cached</v-icon>
        </span>
      </template>
    </v-btn>
  </div>
</validation-observer>
</template>

<script>

import Provider from '@/api/imap_migration/providers'

export default {
  props: ['value'],
  data () {
    return {
      form: {},
      connectionStatus: 0,
      loading: false
    }
  },
  methods: {
    reset () {
      this.form = {}
    },
    async checkConnection () {
      if (await this.validateForm()) {
        this.loading = true
        const params = {
          address: this.form.address,
          port: this.form.port,
          secured: this.form.secured
        }
        Provider.checkProvider(params).then(response => {
          this.connectionStatus = 1
          this.loading = false
        }).catch(error => {
          console.log(error)
          this.loading = false
          this.connectionStatus = 2
        })
      }
    },
    async validateForm () {
      return await this.$refs.observer.validate()
    },
    update () {
      this.connectionStatus = 0
      console.log(this.form)
      this.$emit('input', this.form)
    }
  },
  watch: {
    value: {
      handler (newValue) {
        this.form = { ...newValue }
      },
      immediate: true
    }
  }
}
</script>

<style>
  .custom-loader {
    animation: loader 1s infinite;
    display: flex;
  }
  @-moz-keyframes loader {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(360deg);
    }
  }
  @-webkit-keyframes loader {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(360deg);
    }
  }
  @-o-keyframes loader {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(360deg);
    }
  }
  @keyframes loader {
    from {
      transform: rotate(0);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
