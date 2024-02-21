<template>
  <v-form ref="vFormRef">
    <label class="m-label">{{ $gettext('Username') }}</label>
    <EmailField
      ref="username"
      v-model="account.username"
      :placeholder="usernamePlaceholder"
      :type="usernameInputType"
      :rules="
        usernameInputType === 'email'
          ? [rules.required, rules.email]
          : [rules.required]
      "
      :role="account.role"
      :error-msg="formErrors.value ? formErrors.value.username : []"
      @update:model-value="updateUsername"
    />
    <label class="m-label">{{ $gettext('First name') }}</label>
    <v-text-field
      v-model="account.first_name"
      autocomplete="new-password"
      variant="outlined"
      density="compact"
    />
    <label class="m-label">{{ $gettext('Last name') }}</label>
    <v-text-field
      v-model="account.last_name"
      autocomplete="new-password"
      variant="outlined"
      density="compact"
    />

    <AccountPasswordSubForm
      ref="passwordForm"
      v-model="account"
      :editing="editing"
      :form-errors="formErrors"
    />

    <v-switch
      v-model="account.is_active"
      :label="$gettext('Enabled')"
      density="compact"
      color="primary"
    />
  </v-form>
</template>

<script setup lang="js">
import AccountPasswordSubForm from './AccountPasswordSubForm.vue'
import EmailField from '@/components/tools/EmailField.vue'
import { ref, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import rules from '@/plugins/rules'

const { $gettext } = useGettext()
const props = defineProps({
  modelValue: { type: Object, default: null },
  editing: { type: Boolean, default: false },
})

const vFormRef = ref()
const formErrors = ref({})

const account = computed(() => props.modelValue)

const usernamePlaceholder = computed(() => {
  if (account.value.role === 'SimpleUsers') {
    return $gettext('Enter an email address')
  }
  return $gettext('Enter a simple username or an email address')
})

const usernameInputType = computed(() => {
  return account.value.role === 'SimpleUsers' ? 'email' : 'text'
})

function updateUsername() {
  if (
    account.value.role != 'SuperAdmins' &&
    account.value.username.indexOf('@') !== -1
  ) {
    account.value.mailbox.full_address = account.value.username
    account.value.mailbox.message_limit = null
  }
}

defineExpose({ vFormRef, formErrors })
</script>
