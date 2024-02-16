<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col
        cols="12"
        sm="10"
        md="8"
        class="text-center"
        @keyup.enter="recoverPassword"
      >
        <h4 class="text-primary mb-10 text-h4">
          {{ $gettext('Forgot password?') }}
        </h4>
        <v-form ref="observer" class="my-4">
          <label class="m-label">{{
            $gettext('Please fill-in your primary email address')
          }}</label>
          <v-text-field
            v-model="email"
            variant="outlined"
            :rules="[rules.required, rules.email]"
            :error-messages="errors"
          />
        </v-form>
        <div class="d-flex justify-center">
          <v-btn
            class="flex-grow-1"
            color="primary"
            size="large"
            :loading="loading"
            @click="recoverPassword"
          >
            {{ $gettext('Submit') }}
          </v-btn>
        </div>
        <div>
          <a class="float-right text-primary" @click="returnToLogin">{{
            $gettext('Return to login')
          }}</a>
        </div>
      </v-col>
      <ConfirmDialog ref="dialog" />
    </v-row>
  </v-container>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'

import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

import auth from '@/api/auth'
import rules from '@/plugins/rules.js'

const router = useRouter()
const { $gettext } = useGettext()
const loading = ref(false)
const email = ref('')
const dialog = ref(null)
const observer = ref(null)
const errors = ref([])

function returnToLogin() {
  router.push({ name: 'Login' })
}

async function showDialog(title, body, error = false) {
  let color = 'info'
  if (error) {
    color = 'error'
  }
  const confirm = await dialog.value.open(title, body, {
    color: color,
    cancelLabel: $gettext('Ok'),
    agreeLabel: $gettext('Return to login'),
  })
  if (!confirm) {
    return
  }
  returnToLogin()
}

async function recoverPassword() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  const payload = {
    email: email.value,
  }
  loading.value = true
  auth
    .recoverPassword(payload)
    .then(async (resp) => {
      loading.value = false
      if (resp.status === 200) {
        if (resp.data.type === 'sms') {
          router.push({ name: 'PasswordRecoverySmsTotpForm' })
        } else if (resp.data.type === 'email') {
          await showDialog(
            'Info',
            $gettext('Email sent, please check your inbox')
          )
        }
      }
    })
    .catch((err) => {
      loading.value = false
      if (err.response.status === 404) {
        if (
          err.response.data.type === 'sms' ||
          err.response.data.type === 'email'
        ) {
          errors.value = [$gettext(err.response.data.reason)]
        }
      } else if (
        err.response.status === 503 &&
        err.response.data.type === 'email'
      ) {
        showDialog('Error', err.response.data.reason, true)
      } else if (err.response.status === 429) {
        errors.value = [
          $gettext('Too many unsuccessful attempts, please try later.'),
        ]
      }
    })
}
</script>
