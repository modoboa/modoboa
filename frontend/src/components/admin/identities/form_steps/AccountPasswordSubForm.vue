<template>
  <div>
    <template v-if="withPasswordCheck">
      <label class="m-label">{{ $gettext('Current password') }}</label>
      <v-text-field
        v-model="account.password"
        autocomplete="new-password"
        variant="outlined"
        type="password"
        density="compact"
        validate-on="submit"
        :rules="disabled ? [] : [rules.required]"
        :disabled="disabled"
        :error-messages="props.formErrors ? props.formErrors.password : []"
      />
    </template>
    <v-row justify="center">
      <v-col cols="auto">
        <v-switch
          v-model="account.random_password"
          :label="$gettext('Random password')"
          density="compact"
          color="primary"
          class="text-center"
          :disabled="disabled"
          @update:model-value="updatePassword"
        />
      </v-col>
      <v-col>
        <v-alert
          v-if="account.random_password"
          style="background-color: #515d78"
          class="ml-6"
          density="compact"
        >
          <span class="text-white mr-4">{{ account.new_password }}</span>
          <v-btn
            size="small"
            color="white"
            variant="text"
            density="compact"
            :disabled="disabled"
            icon="mdi-clipboard-multiple-outline"
            :title="$gettext('Copy to clipboard')"
            @click="copyPassword"
          />
        </v-alert>
      </v-col>
    </v-row>
    <template v-if="!account.random_password">
      <v-text-field
        v-model="account.new_password"
        variant="outlined"
        :label="$gettext('Password')"
        type="password"
        autocomplete="new-password"
        density="compact"
        :disabled="disabled"
        :rules="isRuleActive ? [rules.required] : []"
      />
      <v-text-field
        v-model="account.password_confirmation"
        variant="outlined"
        type="password"
        :label="$gettext('Confirmation')"
        density="compact"
        :disabled="disabled"
        :rules="isRuleActive ? [rules.required, passwordConfirmationRules] : []"
        :error-messages="props.formErrors ? props.formErrors.new_password : []"
      />
    </template>
  </div>
</template>

<script setup lang="js">
import { useBusStore } from '@/stores'
import accountsApi from '@/api/accounts'
import { computed } from 'vue'
import rules from '@/plugins/rules'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
const busStore = useBusStore()
const props = defineProps({
  modelValue: { type: Object, default: null },
  withPasswordCheck: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  editing: { type: Boolean, default: false },
  formErrors: { type: Object, required: false, default: () => {} },
})

const account = computed(() => props.modelValue)

const isRuleActive = computed(
  () => !props.disabled && (!props.editing || account.value.password)
)

const passwordConfirmationRules = (value) =>
  value === account.value.new_password || $gettext('Password mismatch')

function copyPassword() {
  navigator.clipboard.writeText(account.value.new_password).then(() => {
    busStore.displayNotification({
      msg: $gettext('Password copied to clipboard'),
    })
  })
}

function updatePassword(value) {
  if (value) {
    accountsApi.getRandomPassword().then((resp) => {
      account.value.new_password = resp.data.password
    })
  } else {
    account.value.new_password = null
    account.value.password_confirmation = null
  }
}
</script>
