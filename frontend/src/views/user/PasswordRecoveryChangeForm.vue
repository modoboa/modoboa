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
        <p id="password_validation">{{ password_validation_error }}</p>
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
        <router-link :to="{ name: 'Login' }" class="float-right primary--text">
          <translate>Return to login</translate>
        </router-link>
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
      password_validation_error: '',
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
          this.$router.push({ name: 'PasswordRecoveryForm' })
        } else {
          this.id = this.$route.params.id
          this.token = this.$route.params.token
          this.$router.push({ name: 'PasswordRecoveryChangeForm' })
        }
      }
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
      this.password_validation_error = ''
      auth.changePassword(payload).then(resp => {
        if (resp.status === 200) {
          this.loading = false
          this.returnLogin()
        }
      }).catch(err => {
        let message = ''
        this.loading = false
        if (err.response.status === 403) {
          message = this.$gettext('Invalid reset token.')
        } else if (err.response.status === 404) {
          message = this.$gettext('User unknown.')
        } else if (err.response.status === 400 && err.response.data.type === 'password_requirement') {
          err.response.data.errors.forEach(element => {
            message += this.$gettext(element) + '<br>'
          })
        } else if (err.response.status === 429) {
          message = this.$gettext('Too many unsuccessful attempts, please try later.')
        }
        this.password_validation_error = message
      })
    }
  },
  beforeMount () {
    this.checkUrl()
  }
}
</script>

<style>
#password_validation {
  color:crimson;
}
</style>
