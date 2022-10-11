<template>
  <v-row style="height: 100%; margin: 0 auto">
    <v-col cols="0" sm="6" class="primary" style="height: 100%">
      <v-img
        src="../../assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="300"
        class="mt-10 ml-8"
        />
    </v-col>
    <v-col cols="12" sm="6" class="d-flex flex-column justify-center pa-10" @keyup.enter="changePassword">
      <span class="primary--text mb-6 text-h4"><translate>Forgot password?</translate></span>
      <validation-observer ref="observer">
        <validation-provider
          vid="password"
          v-slot="{ errors }"
          rules="required"
        >
        <label class="m-label"><translate>Change password</translate></label>
          <v-text-field
            v-model="password"
            :error-messages="errors"
            type="password"
            outlined
            />
        </validation-provider>
        <validation-provider
          vid="password_confirm"
          v-slot="{ errors }"
          rules="required|samePassword:password"
        >
          <v-text-field
            v-model="password_confirmed"
            :error-messages="errors"
            type="password"
            outlined
            />
        </validation-provider>
      </validation-observer>
      <div class="d-flex justify-center">
        <v-btn
          class="flex-grow-1"
          color="primary"
          large
          @click="changePassword"
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
      password: '',
      password_confirmed: '',
      errors: {}
    }
  },
  methods: {
    checkUrl: function () {
      const decodedId = atob(this.$route.params.id)
      if (!/^\d+$/.test(decodedId) || this.$route.params.token !== 'set-password') {
        this.$router.push({ name: 'Login' })
      }
    },
    returnLogin () {
      this.$router.push({ name: 'Login' })
    },
    async changePassword () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      const payload = {
        new_password1: this.password,
        new_password2: this.password_confirmed
      }
      this.loading = true
      auth.changePassword(payload, this.$route.params.id, this.$route.params.token).then(resp => {
        this.loading = false
        this.$router.push({ name: 'PasswordRecoveryDone', params: { data: { fail: false } } })
      }).catch(err => {
        this.loading = false
        if (err.response.status === 400) {
          this.$refs.observer.setErrors({
            email: this.$gettext('Invalid email')
          })
        }
      })
    }
  },
  beforeMount () {
    this.checkUrl()
  }
}
</script>

<style>
</style>
