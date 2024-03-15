<script setup lang="js">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'

import { useAuthStore } from '@/stores'
import rules from '@/plugins/rules.js'

const loading = ref(false)
const rememberMe = ref(false)
const username = ref('')
const password = ref('')
const isPasswordvisible = ref(false)
const loginForm = ref()
const errors = ref([])

const authStore = useAuthStore()
const router = useRouter()
const { $gettext } = useGettext()

async function authenticate() {
  const { valid } = await loginForm.value.validate()
  if (!valid) {
    return
  }
  loading.value = true

  const payload = {
    username: username.value,
    password: password.value,
    rememberMe: rememberMe.value,
  }
  authStore
    .login(payload)
    .then(() => {
      if (authStore.authUser.role === 'SimpleUsers') {
        router.push({ name: 'AccountSettings' })
      } else {
        router.push({ name: 'Dashboard' })
      }
    })
    .catch((err) => {
      loading.value = false
      if (err.response.status === 401) {
        errors.value = [$gettext('Invalid username and/or password')]
      } else if (err.response.status === 429) {
        errors.value = [
          $gettext('Too many unsuccessful attempts, please try later.'),
        ]
      }
    })
}
</script>

<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="8" class="text-center">
        <h4 class="text-primary mb-10 text-h4">
          {{ $gettext('Identification') }}
        </h4>
        <v-form ref="loginForm" @submit.prevent="authenticate">
          <v-text-field
            v-model="username"
            variant="outlined"
            :label="$gettext('Username')"
            prepend-inner-icon="mdi-account-outline"
            :rules="[rules.required]"
          />
          <v-text-field
            v-model="password"
            :type="isPasswordvisible ? 'text' : 'password'"
            prepend-inner-icon="mdi-lock-outline"
            :label="$gettext('Password')"
            variant="outlined"
            :append-inner-icon="isPasswordvisible ? 'mdi-eye-off' : 'mdi-eye'"
            :rules="[rules.required, rules.minLength(6)]"
            :error-messages="errors"
            @click:append-inner="isPasswordvisible = !isPasswordvisible"
          />
          <v-checkbox v-model="rememberMe" :label="$gettext('Remember me')" />

          <v-btn
            block
            color="primary"
            size="large"
            type="submit"
            :loading="loading"
            class="mb-5"
          >
            {{ $gettext('Connect') }}
          </v-btn>
        </v-form>
        <v-btn
          block
          variant="outlined"
          size="large"
          :to="{ name: 'PasswordRecovery' }"
        >
          {{ $gettext('Forgot password') }}
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>
