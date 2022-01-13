<template>
<v-row style="height: 100%; margin: 0 auto">
  <v-col cols="0" sm="6" class="primary" style="height: 100%">
    <v-img
      src="../assets/Modoboa_RVB-BLANC-SANS.png"
      max-width="300"
      class="mt-10 ml-8"
      />
  </v-col>
  <v-col cols="12" sm="6" class="d-flex flex-column justify-center pa-10" @keyup.enter="verifyCode">
    <span class="primary--text mb-6 text-h4"><translate>Verification</translate></span>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        vid="code"
        rules="required"
        >
        <v-row>
          <v-col cols="6" offset="3">
            <label class="m-label"><translate>Two-factor authentication code</translate></label>
            <v-otp-input
              v-model="code"
              length="6"
              :error-messages="errors"
              :hint="'Enter the code from the two-factor app on your mobile device. If you have lost your device, you may enter one of your recovery codes.'|translate"
              persistent-hint
              />
          </v-col>
        </v-row>
      </validation-provider>
    </validation-observer>
    <div class="d-flex justify-center mt-6">
      <v-btn class="flex-grow-1" color="primary" large @click="verifyCode">
        <translate>Verify code</translate>
      </v-btn>
    </div>
  </v-col>
</v-row>
</template>

<script>
import Cookies from 'js-cookie'
import account from '@/api/account'

export default {
  data () {
    return {
      code: null,
      errors: {}
    }
  },
  methods: {
    async verifyCode () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) {
        return
      }
      account.verifyTFACode(this.code).then(resp => {
        Cookies.set('token', resp.data.access, { sameSite: 'strict' })
        Cookies.set('refreshToken', resp.data.refresh, { sameSite: 'strict' })
        this.$store.dispatch('auth/initialize').then(() => {
          this.$router.push({ name: 'DomainList' })
        })
      }).catch(error => {
        this.$refs.observer.setErrors(error.response.data)
      })
    }
  }
}
</script>
