<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col
        cols="12"
        sm="6"
        class="d-flex flex-column justify-center pa-10"
        @keyup.enter="changePassword"
      >
        <ConfirmDialog ref="confirm" />
        <h4 class="text-primary mb-6 text-h4">
          {{ $gettext('Password recovery') }}
        </h4>
        <v-form ref="observer">
          <label class="m-label"
            >{{ $gettext("Enter the code you've just received by SMS") }}
          </label>
          <v-text-field
            v-model="sms_totp"
            type="totp"
            variant="outlined"
            :rules="[rules.required, (value) => rules.length(value, 6)]"
            :error-messages="errors"
          />
        </v-form>
        <div class="d-flex justify-center">
          <v-btn
            class="flex-grow-1"
            color="primary"
            size="large"
            :loading="loading"
            @click="checkSmsTotp"
          >
            {{ $gettext('Submit') }}
          </v-btn>
        </div>
        <div>
          <a class="float-left text-primary" @click="resendSms">{{
            $gettext('Resend SMS.')
          }}</a>
          <router-link
            :to="{ name: 'Login' }"
            class="float-right text-primary"
            >{{ $gettext('Return to login') }}</router-link
          >
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="js">
import { ref } from 'vue'
import auth from '@/api/auth'
import rules from '@/plugins/rules.js'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'

import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const { $gettext } = useGettext()
const router = useRouter()
const confirm = ref(null)
const loading = ref(false)
const observer = ref(null)
const sms_totp = ref('')
const errors = ref([])

async function showErrorDialog(body) {
  const confirm = await confirm.value.open($gettext('Error'), body, {
    color: 'error',
    cancelLabel: $gettext('Return to login'),
    agreeLabel: $gettext('Retry reset'),
  })
  if (!confirm) {
    router.push({ name: 'Login' })
  } else {
    router.push({ name: 'PasswordRecoveryForm' })
  }
}

async function resendSms() {
  auth
    .checkSmsTotp({ type: 'resend' })
    .then((resp) => {
      loading.value = false
      if (resp.status === 200) {
        observer.value.setErrors({
          sms_totp: this.$gettext('TOTP resent.'),
        })
      }
    })
    .catch(async (err) => {
      if (err.response.status === 400) {
        this.loading = false
        await showErrorDialog(
          $gettext(
            'User seems wrong, return to login or restart reset the process?'
          )
        )
      } else if (err.response.status === 429) {
        errors.value = [
          $gettext('Too many unsuccessful attempts, please try later.'),
        ]
      }
    })
}

async function checkSmsTotp() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  const payload = {
    type: 'confirm',
    sms_totp: this.sms_totp,
  }
  loading.value = true
  auth
    .checkSmsTotp(payload)
    .then((resp) => {
      loading.value = false
      if (resp.status === 200) {
        // Code is good, redirecting to change password form.
        router.push({
          name: 'PasswordRecoveryChangeForm',
          data: resp.response.data,
        })
      }
    })
    .catch(async (err) => {
      loading.value = false
      if (err.response.status === 403 && 'reason' in err.response.data) {
        await showErrorDialog(err.response.data.reason)
      } else if (err.response.status === 400 && 'reason' in err.response.data) {
        errors.value = [$gettext(err.response.data.reason)]
      }
    })
}
</script>
