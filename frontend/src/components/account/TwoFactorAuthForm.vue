<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-subtitle-1">
          {{ $gettext('Two factor authentication') }}
        </span>
      </v-card-title>
      <v-card-text>
        <template v-if="qrURL">
          <v-row>
            <v-col cols="4">
              <v-row rows="2">
                <QrcodeVue
                  :value="qrURL"
                  :size="250"
                  render-as="svg"
                  level="H"
                  class="qrcode"
                />
              </v-row>
              <v-row>
                <v-btn color="primary" class="key" @click="copyKey">
                  {{ $gettext('Click here to copy the key') }}
                  <v-icon v-if="clicked" color="success">
                    mdi-check-all
                  </v-icon>
                </v-btn>
              </v-row>
            </v-col>
            <v-col cols="6">
              <v-alert type="info" class="ma-4">
                {{
                  $gettext(
                    'Install a soft token authenticator like FreeOTP or Google Authenticator from your application repository and use that app to scan this QR code.'
                  )
                }}
              </v-alert>
              <label class="m-label">{{ $gettext('Pin code') }}</label>
              <v-otp-input v-model="pinCode" />
              <v-btn color="primary" @click="finalizeTFASetup">
                {{ $gettext('Register') }}
              </v-btn>
            </v-col>
          </v-row>
        </template>
        <template v-else-if="tokens.length">
          <v-alert type="success">
            {{
              $gettext(
                'Congratulations! Two-Factor Authentication is now enabled for your account.'
              )
            }}
          </v-alert>
          <p>
            {{
              $gettext(
                "The following recovery codes can be used one time each to let you regain access to your account, in case you lose your phone for example. Make sure to save them in a safe place, otherwise you won't be able to access your account anymore."
              )
            }}
          </p>
          <ul>
            <li v-for="token in tokens" :key="token">
              {{ token }}
            </li>
          </ul>
        </template>
        <template v-else-if="tfa_enabled">
          <v-alert type="info">
            {{
              $gettext('Two-Factor Authentication is enabled for your account.')
            }}
          </v-alert>
          <v-form ref="editTFAForm">
            <label class="m-label">{{ $gettext('Password') }} </label>
            <v-text-field
              v-model="password"
              type="password"
              variant="outlined"
              :rules="[rules.required]"
              :error-messages="passwordError"
            />
            <div class="mt-5">
              <v-btn
                color="error"
                class="mr-2"
                :loading="loadingDisable"
                @click="disableTFA"
              >
                {{ $gettext('Disable 2FA') }}
              </v-btn>
              <v-btn :loading="loadingReset" @click="resetRecoveryCodes">
                {{ $gettext('Reset recovery codes') }}
              </v-btn>
            </div>
          </v-form>
        </template>
        <template v-else>
          <div tag="p" class="my-4">
            {{
              $gettext(
                "Two-Factor Authentication (2FA) is not yet activated for your account. Enabling this feature will increase your account's security."
              )
            }}
          </div>
          <v-btn color="success" @click="startTFASetup">
            {{ $gettext('Enable 2FA') }}
          </v-btn>
        </template>
      </v-card-text>
    </v-card>
    <v-dialog v-model="showCodesResetDialog" max-width="800px" persistent>
      <RecoveryCodesResetDialog
        :tokens="newTokens"
        @close="closeRecoveryCodesResetDialog"
      />
    </v-dialog>
  </div>
</template>

<script setup lang="js">
import accountApi from '@/api/account'
import RecoveryCodesResetDialog from './RecoveryCodesResetDialog'
import QrcodeVue from 'qrcode.vue'
import { useBusStore, useAuthStore } from '@/stores'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules'

const { $gettext } = useGettext()
const busStore = useBusStore()
const authStore = useAuthStore()

const editTFAForm = ref()

const newTokens = ref([])
const pinCode = ref('')
const pinCodeErrors = ref()
const key = ref(null)
const qrURL = ref(null)
const clicked = ref(false)
const showCodesResetDialog = ref(false)
const loadingDisable = ref(false)
const loadingReset = ref(false)
const password = ref('')
const passwordError = ref()
const tokens = ref([])

const tfa_enabled = computed(() => authStore.authUser.tfa_enabled)

function getKey() {
  accountApi.getKeyForTFASetup().then((resp) => {
    key.value = resp.data.key
    qrURL.value = resp.data.url
  })
}

function copyKey() {
  navigator.clipboard.writeText(key.value)
  clicked.value = true
}

function startTFASetup() {
  accountApi.startTFASetup().then(() => {
    getKey()
  })
}

async function finalizeTFASetup() {
  authStore
    .finalizeTFASetup(pinCode.value)
    .then((response) => {
      key.value = null
      qrURL.value = null
      tokens.value = response.data.tokens
    })
    .catch((error) => {
      if (error.response.status === 400) {
        pinCodeErrors.value = error.response.data
      }
    })
}

async function disableTFA() {
  const isValid = await editTFAForm.value.validate()
  if (!isValid) {
    return
  }
  const payload = {
    password: password.value,
  }
  loadingDisable.value = true
  accountApi
    .disableTFA(payload)
    .then(() => {
      authStore.fetchUser()
    })
    .catch((error) => {
      if (error.response.status === 400) {
        passwordError.value = error.response.data
      } else {
        busStore.displayNotification({
          msg: $gettext(error.response.data),
          type: 'error',
        })
      }
    })
    .finally(() => {
      loadingDisable.value = false
      editTFAForm.value.reset()
    })
}

async function resetRecoveryCodes() {
  const isValid = await editTFAForm.value.validate()
  if (!isValid) {
    return
  }
  const payload = {
    password: password.value,
  }
  loadingReset.value = true

  accountApi
    .resetRecoveryCodes(payload)
    .then((response) => {
      newTokens.value = response.data.tokens
      showCodesResetDialog.value = true
    })
    .catch((error) => {
      if (error.response.status === 400) {
        passwordError.value = error.response.data
      } else {
        busStore.displayNotification({
          msg: $gettext(error.response.data),
          type: 'error',
        })
      }
    })
    .finally(() => {
      loadingReset.value = false
      editTFAForm.value.reset()
    })
}

function closeRecoveryCodesResetDialog() {
  newTokens.value = []
  showCodesResetDialog.value = false
}
if (!tfa_enabled.value) {
  getKey()
}
</script>

<style>
.qrcode {
  margin-left: 20px;
  margin-top: 2em;
}
.key {
  margin-left: 10px;
  margin-top: 1.75em;
}
</style>
