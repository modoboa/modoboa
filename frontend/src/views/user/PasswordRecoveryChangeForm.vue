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
      errors: {},
      token: '',
      id: ''
    }
  },
  methods: {
    checkUrl: function () {
      if (this.$route.params.token === undefined) {
        if (this.token === '' || this.id === '') {
          this.$router.push({ name: 'PasswordRecoveryForm' })
        }
      } else {
        const decodedId = atob(this.$route.params.id)
        if (!/^\d+$/.test(decodedId)) {
          console.error('ID passed does not seems to be an integer !')
          this.$router.push({ name: 'PasswordRecoveryForm' })
        } else {
          this.id = this.$route.params.id
          this.token = this.$route.params.token
          this.$router.push({ name: 'PasswordRecoveryChangeForm' })
        }
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
        new_password2: this.password_confirmed,
        token: this.token,
        id: this.id
      }
      this.loading = true
      auth.changePassword(payload).then(resp => {
        this.loading = false
        this.$router.push({ name: 'PasswordRecoveryDone' })
      }).catch(err => {
        this.loading = false
        if (err.response.status === 400) {
          this.$refs.observer.setErrors({
            password_confirmed: this.$gettext('Invalid email.')
          })
        } else if (err.response.status === 401) {
          this.$refs.observer.setErrors({
            password_confirmed: this.$gettext('Invalid reset token.')
          })
        } else if (err.response.status === 404) {
          this.$refs.observer.setErrors({
            password_confirmed: this.$gettext('User unknown.')
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
