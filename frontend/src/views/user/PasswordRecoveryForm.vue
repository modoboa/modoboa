<template>
  <v-row style="height: 100%; margin: 0 auto">
    <v-col cols="0" sm="6" class="primary" style="height: 100%">
      <v-img
        src="../../assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="300"
        class="mt-10 ml-8"
        />
    </v-col>
    <v-col cols="12" sm="6" class="d-flex flex-column justify-center pa-10" @keyup.enter="recoverPassword">
      <span class="primary--text mb-6 text-h4"><translate>Forgot password?</translate></span>
      <validation-observer ref="observer">
        <validation-provider
          vid="email"
          v-slot="{ errors }"
          rules="required|email"
        >
        <label class="m-label"><translate>Please fill-in your primary email address</translate></label>
          <v-text-field
            v-model="email"
            :error-messages="errors"
            outlined
            />
        </validation-provider>
      </validation-observer>
      <div class="d-flex justify-center">
        <v-btn
          class="flex-grow-1"
          color="primary"
          large
          @click="recoverPassword"
          :loading="loading"
          >
          <translate>Submit</translate>
        </v-btn>
      </div>
      <div>
        <a @click="returnLogin" class="float-right primary--text"><translate>Return to login?</translate></a>
      </div>
    </v-col>
  </v-row>
</template>

<script>
import auth from '@/api/auth'

export default {
  data () {
    return {
      loading: false,
      email: '',
      errors: {}
    }
  },
  methods: {
    returnLogin () {
      this.$router.push({ name: 'Login' })
    },
    async recoverPassword () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      const payload = {
        email: this.email
      }
      this.loading = true
      auth.recoverPassword(payload).then(resp => {
        this.loading = false
        this.returnLogin()
      }).catch(err => {
        this.loading = false
        if (err.response.status === 400) {
          this.$refs.observer.setErrors({
            email: this.$gettext('Invalid email')
          })
        }
      })
    }
  }
}
</script>

<style>
</style>
