<template>
  <v-row style="height: 100%; margin: 0 auto">
    <v-col cols="0" sm="6" class="primary" style="height: 100%">
      <v-img
        src="@/assets/Modoboa_RVB-BLANC-SANS.png"
        max-width="300"
        class="mt-10 ml-8"
      />
    </v-col>
    <v-col
      cols="12"
      sm="6"
      class="d-flex flex-column justify-center pa-10"
      @keyup.enter="recoverPassword"
    >
      <span class="text-primary mb-6 text-h4">{{
        $gettext('Forgot password?')
      }}</span>
      <v-form ref="observer">
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
        <a :to="{ name: 'Login' }" class="float-right text-primary">{{
          $gettext('Return to login')
        }}</a>
      </div>
    </v-col>
    <ConfirmDialog ref="confirm" />
  </v-row>
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
const confirm = ref(null)
const errors = ref([])

async function showDialog(title, body, error = false) {
  let color = 'info'
  if (error) {
    color = 'error'
  }
  const result = await confirm.value.open(title, body, {
    color: color,
    cancelLabel: $gettext('Ok'),
    agreeLabel: $gettext('Return to login'),
  })
  if (!result) {
    return
  }
  router.push({ name: 'Login' })
}

async function recoverPassword() {
  const { valid } = await this.$refs.observer.validate()
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
          router.push({ name: 'PasswordRecoverySms' })
        } else if (resp.data.type === 'email') {
          await showDialog(
            $gettext('Info'),
            $gettext('Email sent, please check your inbox')
          )
        }
      }
    })
    .catch(async (err) => {
      loading.value = false
      if (err.response.status === 404) {
        if (
          err.response.data.type === 'sms' ||
          err.response.data.type === 'email'
        ) {
          errors.value = [err.response.data.reason]
        }
      } else if (
        err.response.status === 503 &&
        err.response.data.type === 'email'
      ) {
        await showDialog($gettext('Error'), err.response.data.reason, true)
      } else if (err.response.status === 429) {
        errors.value = [
          $gettext('Too many unsuccessful attempts, please try later.'),
        ]
      }
    })
}
</script>
