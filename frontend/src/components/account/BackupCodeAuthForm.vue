<template>
  <div>
    <v-card flat>
      <v-card-title>
        <span class="text-h6">
          {{ $gettext('Backup codes') }}
        </span>
      </v-card-title>
      <v-card-text>
        <template v-if="tfa_enabled">
          <v-alert type="info" class="mb-2">
            {{
              $gettext(
                "You already have generated backup codes for this account. If you don't remember them or have used them all, you can generate new ones."
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
                :loading="loadingReset"
                color="success"
                @click="resetRecoveryCodes"
              >
                {{ $gettext('Reset recovery codes') }}
              </v-btn>
            </div>
          </v-form>
        </template>
        <template v-else>
          <div tag="p" class="my-4">
            {{
              $gettext(
                'No two-factor authentificator is yet set for your account.'
              )
            }}
          </div>
        </template>
        <v-dialog v-model="showCodesResetDialog" max-width="800px" persistent>
          <RecoveryCodesResetDialog
            :tokens="newTokens"
            @close="closeRecoveryCodesResetDialog"
          />
        </v-dialog>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="js">
import accountApi from '@/api/account'
import RecoveryCodesResetDialog from './RecoveryCodesResetDialog'
import { useGettext } from 'vue3-gettext'
import { useBusStore, useAuthStore } from '@/stores'
import rules from '@/plugins/rules'
import { ref, computed } from 'vue'

const { $gettext } = useGettext()
const busStore = useBusStore()
const authStore = useAuthStore()

const tfa_enabled = computed(() => authStore.authUser.tfa_enabled)

const loadingReset = ref(false)
const editTFAForm = ref()
const password = ref('')
const newTokens = ref([])
const passwordError = ref()
const showCodesResetDialog = ref(false)

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
        passwordError.value = error.response.data.password
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
</script>
