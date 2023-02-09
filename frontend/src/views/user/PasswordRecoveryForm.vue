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
        <a @click="returnLogin" class="float-right primary--text"><translate>Return to login</translate></a>
      </div>
    </v-col>
    <confirm-dialog ref="dialog_response">
    </confirm-dialog>
  </v-row>
</template>

<script>
import auth from '@/api/auth'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  components: {
    ConfirmDialog
  },
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
    async showDialog (title, body, error = false) {
      let color = 'info'
      if (error) {
        color = 'error'
      }
      const confirm = await this.$refs.dialog_response.open(
        this.$gettext(title),
        this.$gettext(
          body
        ),
        {
          color: color,
          cancelLabel: this.$gettext('Ok'),
          agreeLabel: this.$gettext('Return to login')
        })
      if (!confirm) {
        return
      }
      this.returnLogin()
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
        if (resp.status === 200) {
          if (resp.data.type === 'sms') {
            this.$router.push({ name: 'PasswordRecoverySmsTotpForm' })
          } else if (resp.data.type === 'email') {
            this.showDialog('Info', 'Email sent, please check your inbox')
          }
        }
      }).catch(err => {
        this.loading = false
        if (err.response.status === 404) {
          if (err.response.data.type === 'sms' || err.response.data.type === 'email') {
            this.$refs.observer.setErrors({
              email: this.$gettext(err.response.data.reason)
            })
          }
        } else if (err.response.status === 503 && err.response.data.type === 'email') {
          this.showDialog('Error', err.response.data.reason, true)
        } else if (err.response.status === 429) {
          this.$refs.observer.setErrors({
            email: this.$gettext('Too many unsuccessful attempts, please try later.')
          })
        }
      })
    }
  }
}
</script>

<style>
</style>
