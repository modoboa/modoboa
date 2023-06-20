<template>
<div>
  <v-card flat>
    <v-card-title>
      <span class="text-subtitle-1"><translate>Two factor authentication</translate></span>
    </v-card-title>
    <v-card-text>
      <template v-if="qrURL">
        <v-row>
          <v-col cols="4">
            <v-row rows="2">
              <qrcode-vue
              :value="qrURL"
              :size="200"
              render-as="svg"
              level="H"
              class= "qrcode"
              />
            </v-row>
            <v-row>
              <v-btn color="primary" @click="copyKey" class="key">
                Click here to copy the key
                <v-icon
                  v-if="clicked"
                  color="success"
                >
        mdi-check-all
      </v-icon>
              </v-btn>
            </v-row>
          </v-col>
          <v-col cols="6">
            <v-alert type="info">
              <translate>
                Install a soft token authenticator like FreeOTP or Google
                Authenticator from your application repository and use that
                app to scan this QR code.
              </translate>
            </v-alert>
            <label class="m-label"><translate>Pin code</translate></label>
            <validation-observer ref="observer">
              <validation-provider
                v-slot="{ errors }"
                rules="required"
                >
                <v-text-field
                  v-model="pinCode"
                  outlined
                  :error-messages="errors"
                  />
              </validation-provider>
            </validation-observer>
            <v-btn color="primary" @click="finalizeTFASetup">
              <translate>Register</translate>
            </v-btn>
          </v-col>
        </v-row>
      </template>
      <template v-else-if="tokens.length">
        <v-alert type="success">
          <translate>
            Congratulations! Two-Factor Authentication is now enabled for your account.
          </translate>
        </v-alert>
        <p>
          <translate>
            The following recovery codes can be used one time each to
            let you regain access to your account, in case you lose your
            phone for example. Make sure to save them in a safe place,
            otherwise you won't be able to access your account anymore.
          </translate>
        </p>
        <ul>
          <li v-for="token in tokens" :key="token">
            {{ token }}
          </li>
        </ul>
      </template>
      <template v-else-if="account.tfa_enabled">
        <v-alert type="info">
          Two-Factor Authentication is enabled for your account.
        </v-alert>
        <v-btn color="error" @click="disableTFA" class="mr-2">
          <translate>Disable 2FA</translate>
        </v-btn>
        <v-btn @click="resetRecoveryCodes">
          <translate>Reset recovery codes</translate>
        </v-btn>
      </template>
      <template v-else>
        <translate tag="p" class="my-4">
          Two-Factor Authentication (2FA) is not yet activated for your account. Enabling this feature will increase your account's security.
        </translate>
        <v-btn color="success" @click="startTFASetup">
        <translate>Enable 2FA</translate>
        </v-btn>
      </template>
    </v-card-text>
  </v-card>
  <v-dialog
    v-model="showCodesResetDialog"
    max-width="800px"
    persistent
    >
    <recovery-codes-reset-dialog
      :tokens="newTokens"
      @close="closeRecoveryCodesResetDialog"
      />
  </v-dialog>
</div>
</template>

<script>
import account from '@/api/account'
import Cookies from 'js-cookie'
import RecoveryCodesResetDialog from './RecoveryCodesResetDialog'
import QrcodeVue from 'qrcode.vue'

export default {
  components: {
    RecoveryCodesResetDialog,
    QrcodeVue
  },
  props: {
    account: Object
  },
  data () {
    return {
      newTokens: [],
      pinCode: null,
      key: null,
      qrURL: null,
      clicked: false,
      showCodesResetDialog: false,
      tokens: []
    }
  },
  methods: {
    getKey () {
      account.getKeyForTFASetup().then(resp => {
        this.key = resp.data.key
        this.qrURL = resp.data.url
      })
    },
    copyKey () {
      navigator.clipboard.writeText(this.key)
      this.clicked = true
    },
    startTFASetup () {
      account.startTFASetup().then(resp => {
        this.getKey()
      })
    },
    async finalizeTFASetup () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      const resp = await account.finalizeTFASetup(this.pinCode)
      this.key = null
      this.qrURL = null
      this.tokens = resp.data.tokens
      Cookies.set('token', resp.data.access, { sameSite: 'strict' })
      Cookies.set('refreshToken', resp.data.refresh, { sameSite: 'strict' })
      this.$store.dispatch('auth/initialize')
    },
    disableTFA () {
      account.disableTFA().then(resp => {
        this.$store.dispatch('auth/fetchUser')
      })
    },
    resetRecoveryCodes () {
      account.resetRecoveryCodes().then(resp => {
        this.newTokens = resp.data.tokens
        this.showCodesResetDialog = true
      })
    },
    closeRecoveryCodesResetDialog () {
      this.newTokens = []
      this.showCodesResetDialog = false
    }
  },
  created () {
    if (!this.account.tfa_enabled) {
      this.getKey()
    }
  }
}
</script>

<style>
.qrcode {
  margin-left:20px;
}
.key {
  margin-left:10px;
  margin-top:10px;
}
</style>
