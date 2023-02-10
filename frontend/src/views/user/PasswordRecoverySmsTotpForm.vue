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
      <confirm-dialog ref="confirm_wrong_user">
      </confirm-dialog>
      <span class="primary--text mb-6 text-h4"><translate>Password recovery</translate></span>
      <validation-observer ref="observer">
        <validation-provider
          vid="sms_totp"
          v-slot="{ errors }"
          rules="required|length:6"
        >
        <label class="m-label"><translate>Enter the code you've just received by SMS</translate></label>
          <v-text-field
            v-model="sms_totp"
            :error-messages="errors"
            type="totp"
            outlined
          />
      </validation-provider>
      </validation-observer>
      <div class="d-flex justify-center">
        <v-btn
          class="flex-grow-1"
          color="primary"
          large
          @click="checkSmsTotp"
          :loading="loading"
          >
          <translate>Submit</translate>
        </v-btn>
      </div>
      <div>
        <a @click="resendSms" class="float-left primary--text"><translate>Resend SMS.</translate></a>
        <router-link :to="{ name: 'Login' }" class="float-right primary--text"><translate>Return to login</translate></router-link>
      </div>
    </v-col>
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
      sms_totp: '',
      errors: {}
    }
  },
  methods: {
    async showErrorDialog (body) {
      const confirm = await this.$refs.confirm.open(
        this.$gettext('Error'),
        this.$gettext(body),
        {
          color: 'error',
          cancelLabel: this.$gettext('Return to login'),
          agreeLabel: this.$gettext('Retry reset')
        }
      )
      if (!confirm) {
        this.returnLogin()
      } else {
        this.$router.push({ name: 'PasswordRecoveryForm' })
      }
    },
    async resendSms () {
      auth.checkSmsTotp({ type: 'resend' }).then(resp => {
        this.loading = false
        if (resp.status === 200) {
          this.$refs.observer.setErrors({
            sms_totp: this.$gettext('TOTP resent.')
          })
        }
      }).catch(err => {
        if (err.response.status === 400) {
          this.loading = false
          this.showErrorDialog(this.$t('User seems wrong, return to login or restart reset the process?'))
        } else if (err.response.status === 429) {
          this.$refs.observer.setErrors({
            sms_totp: this.$gettext('Too many unsuccessful attempts, please try later.')
          })
        }
      })
    },
    async checkSmsTotp () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      const payload = {
        type: 'confirm',
        sms_totp: this.sms_totp
      }
      this.loading = true
      auth.checkSmsTotp(payload).then(resp => {
        this.loading = false
        if (resp.status === 200) {
          // Code is good, redirecting to change password form.
          this.$router.push({ name: 'PasswordRecoveryChangeForm', data: resp.response.data })
        }
      }).catch(err => {
        this.loading = false
        if (err.response.status === 403 && 'reason' in err.response.data) {
          this.showErrorDialog(err.response.data.reason)
        } else if (err.response.status === 400 && 'reason' in err.response.data) {
          this.$refs.observer.setErrors({
            sms_totp: this.$gettext(err.response.data.reason)
          })
        }
      })
    }
  }
}
</script>

<style>
</style>
