<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col
        cols="12"
        sm="6"
        class="d-flex flex-column justify-center pa-10"
        @keyup.enter="changePassword"
      >
        <h4 class="text-primary mb-6 text-h4">
          {{ $gettext('Forgot password?') }}
        </h4>
        <v-form ref="observer">
          <p id="password_validation">
            {{ password_validation_error }}
          </p>
          <label class="m-label">{{ $gettext('Change password') }}</label>
          <v-text-field
            v-model="password"
            type="password"
            variant="outlined"
            :rules="[rules.required]"
          />
          <v-text-field
            v-model="password_confirmed"
            type="password"
            variant="outlined"
            :rules="[
              rules.required,
              (value) => rules.samePassword(value, password),
            ]"
          />
        </v-form>
        <div class="d-flex justify-center">
          <v-btn
            class="flex-grow-1"
            color="primary"
            size="large"
            :loading="loading"
            @click="changePassword"
          >
            {{ $gettext('Submit') }}
          </v-btn>
        </div>
        <div>
          <router-link :to="{ name: 'Login' }" class="float-right text-primary">
            {{ $gettext('Return to login') }}
          </router-link>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="js">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'

import auth from '@/api/auth'
import rules from '@/plugins/rules.js'

const { $gettext } = useGettext()
const loading = ref(false)
const password = ref('')
const password_confirmed = ref('')
const password_validation_error = ref('')
const route = useRoute()
const router = useRouter()
const observer = ref(null)

let token
let id

function checkUrl() {
  if (route.params.token === undefined) {
    if (token === '' || id === '') {
      router.push({ name: 'PasswordRecovery' })
    }
  } else {
    const decodedId = atob(route.params.id)
    if (!/^\d+$/.test(decodedId)) {
      router.push({ name: 'PasswordRecovery' })
    } else {
      id = route.params.id
      token = route.params.token
      router.push({ name: 'PasswordRecoveryChangeForm' })
    }
  }
}

async function changePassword() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  const payload = {
    new_password1: password.value,
    new_password2: password_confirmed.value,
    token: token,
    id: id,
  }
  loading.value = true
  password_validation_error.value = ''
  auth
    .changePassword(payload)
    .then((resp) => {
      if (resp.status === 200) {
        loading.value = false
        router.push({ name: 'Login' })
      }
    })
    .catch((err) => {
      let message = ''
      loading.value = false
      if (err.response.status === 403) {
        message = $gettext('Invalid reset token.')
      } else if (err.response.status === 404) {
        message = $gettext('User unknown.')
      } else if (
        err.response.status === 400 &&
        err.response.data.type === 'password_requirement'
      ) {
        err.response.data.errors.forEach((element) => {
          message += $gettext(element) + '<br>'
        })
      } else if (err.response.status === 429) {
        message = $gettext('Too many unsuccessful attempts, please try later.')
      }
      password_validation_error.value = message
    })
}

checkUrl()
</script>

<style>
#password_validation {
  color: crimson;
}
</style>
