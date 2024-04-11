<template>
  <v-container class="fill-height" fuild>
    <v-row align="center" justify="center" dense>
      <v-col cols="12" sm="10" md="8" lg="8" class="text-center">
        <h4 class="text-primary mb-10 text-h4">
          {{ $gettext('Two-factor authentication') }}
        </h4>
        <v-form ref="loginForm" @submit.prevent="verifyCode">
          <div class="text-body-2">
            {{
              $gettext(
                'Enter the code from the two-factor app on your mobile device. If you have lost your device, you may enter one of your recovery codes.'
              )
            }}
          </div>
          <v-otp-input
            ref="otpInput"
            v-model="code"
            length="6"
            :rules="[rules.required]"
            @finish="verifyCode"
          />
          <v-btn
            block
            color="primary"
            size="large"
            type="submit"
            :loading="loading"
            class="mb-5"
          >
            {{ $gettext('Verify code') }}
          </v-btn>
        </v-form>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import account from '@/api/account'
import Cookies from 'js-cookie'
import rules from '@/plugins/rules.js'

const authStore = useAuthStore()
const router = useRouter()
const { $gettext } = useGettext()

const loading = ref(false)
const code = ref('')
const loginForm = ref()

async function verifyCode() {
  const { valid } = await loginForm.value.validate()
  if (!valid) {
    return
  }
  loading.value = true
  account
    .verifyTFACode(code.value)
    .then((resp) => {
      Cookies.set('token', resp.data.access, { sameSite: 'strict' })
      Cookies.set('refreshToken', resp.data.refresh, {
        sameSite: 'strict',
      })
      authStore.initialize().then(() => {
        // bus.$emit('loggedIn')
        router.push({ name: 'DomainList' })
      })
    })
    .catch(() => {
      loading.value = false
    })
}
</script>
