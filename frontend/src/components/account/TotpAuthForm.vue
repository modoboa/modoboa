<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-h6">
          {{ $gettext('One-time passwords') }}
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
              <v-otp-input
                v-model="pinCode"
                :error="pinCodeErrors.length !== 0"
              />
              <v-btn color="primary" @click="finalizeTFASetup">
                {{ $gettext('Register') }}
              </v-btn>
            </v-col>
          </v-row>
        </template>
        <template v-else-if="successSetup">
          <v-alert type="success">
            {{
              $gettext(
                'Congratulations! Two-factor authentication using one-time passwords is now enabled for your account.'
              )
            }}
          </v-alert>
          <template v-if="tokens.length">
            <p class="mt-4">
              {{
                $gettext(
                  "The following recovery codes can be used one time each to let you regain access to your account, in case you lose your phone for example. Make sure to save them in a safe place, otherwise you won't be able to access your account anymore."
                )
              }}
            </p>
            <v-table density="compact">
              <tbody>
                <tr v-for="token in tokens" :key="token">
                  <td>{{ token }}</td>
                </tr>
              </tbody>
            </v-table>
          </template>
        </template>
        <template v-else-if="totp_enabled">
          <v-alert type="info" class="mb-2">
            {{
              $gettext(
                'Two-factor authentication using one-time passwords is enabled for your account.'
              )
            }}
          </v-alert>
          <v-form ref="editTFAForm">
            <label class="m-label">{{ $gettext('Password') }} </label>
            <v-text-field
              v-model="password"
              autocomplete="new-password"
              type="password"
              variant="outlined"
              density="compact"
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
            </div>
          </v-form>
        </template>
        <template v-else>
          <div tag="p" class="my-4">
            {{
              $gettext(
                'Two-factor authentication (2FA) using one-time passwords is not yet activated for your account.'
              )
            }}
          </div>
          <v-btn color="success" @click="startTFASetup">
            {{ $gettext('Register authenticator') }}
          </v-btn>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="js">
import accountApi from '@/api/account'
import QrcodeVue from 'qrcode.vue'
import { useBusStore, useAuthStore } from '@/stores'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules'

const { $gettext } = useGettext()
const busStore = useBusStore()
const authStore = useAuthStore()

const editTFAForm = ref()
const pinCode = ref('')
const pinCodeErrors = ref([])
const key = ref(null)
const qrURL = ref(null)
const clicked = ref(false)
const loadingDisable = ref(false)
const password = ref('')
const passwordError = ref([])
const tokens = ref([])
const successSetup = ref(false)

const totp_enabled = computed(() => authStore.authUser.totp_enabled)

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

function finalizeTFASetup() {
  authStore
    .finalizeTFASetup(pinCode.value)
    .then((response) => {
      key.value = null
      qrURL.value = null
      if (response.status === 200) {
        tokens.value = response.data.tokens
      }
      successSetup.value = true
    })
    .catch((error) => {
      if (error.response.status === 400) {
        pinCodeErrors.value = error.response.data.pin_code
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
        passwordError.value = error.response.data.password
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
