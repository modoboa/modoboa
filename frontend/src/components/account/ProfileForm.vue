<template>
  <v-expansion-panels v-model="panel" flat>
    <v-expansion-panel>
      <v-expansion-panel-title>
        {{ $gettext('General settings') }}
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-form ref="profileForm" @submit.prevent="updateGeneralSettings">
          <label class="m-label">{{ $gettext('First name') }}</label>
          <v-text-field
            v-model="form.first_name"
            variant="outlined"
            density="compact"
          />
          <label class="m-label"> {{ $gettext('Last name') }} </label>
          <v-text-field
            v-model="form.last_name"
            variant="outlined"
            density="compact"
          />
          <label class="m-label">
            {{ $gettext('Language') }}
            <p class="text-disabled">
              {{ $gettext('Feel free to improve the translations') }}
              <a
                href="https://explore.transifex.com/tonio/modoboa/"
                target="_blank"
                >{{ $gettext('here') }}</a
              >
              {{ $gettext('or suggest a new language') }}
              <a
                href="https://github.com/modoboa/modoboa/issues/new/choose"
                target="_blank"
                >{{ $gettext('there') }}</a
              >
            </p>
          </label>
          <v-autocomplete
            v-model="form.language"
            :items="languages"
            item-title="label"
            item-value="code"
            variant="outlined"
            density="compact"
            :error-messages="languageError"
          />
          <label class="m-label">{{ $gettext('Phone number') }}</label>
          <v-text-field
            v-model="form.phone_number"
            :label="$gettext('Phone number')"
            variant="outlined"
            density="compact"
          />
          <label class="m-label">{{ $gettext('Secondary email') }}</label>
          <v-text-field
            v-model="form.secondary_email"
            variant="outlined"
            density="compact"
            :rules="[rules.emailOrNull]"
          />
          <v-btn color="success" type="submit" :loading="loadingUpdateProfile">
            {{ $gettext('Update settings') }}
          </v-btn>
        </v-form>
      </v-expansion-panel-text>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-title>
        {{ $gettext('Password') }}
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-form ref="passwordForm" @submit.prevent="updatePassword">
          <AccountPasswordForm v-model="form" with-password-check />
          <v-btn color="success" type="submit" :loading="loadingPasswordUpdate">
            {{ $gettext('Update Password') }}
          </v-btn>
        </v-form>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="js">
import { useBusStore, useAuthStore } from '@/stores'
import languagesApi from '@/api/languages'
import AccountPasswordForm from '@/components/admin/identities/form_steps/AccountPasswordSubForm.vue'
import { useGettext } from 'vue3-gettext'
import { ref, computed, onMounted, watch } from 'vue'
import rules from '@/plugins/rules'

const { $gettext, available } = useGettext()
const busStore = useBusStore()
const authStore = useAuthStore()

const account = computed(() => authStore.authUser)

const form = ref({})
const profileForm = ref()
const passwordForm = ref()
const languages = ref([])
const panel = ref(0)
const loadingUpdateProfile = ref(false)
const loadingPasswordUpdate = ref(false)
const languageError = ref('')

function initFormFromAccount(account) {
  form.value = {
    first_name: account.first_name,
    last_name: account.last_name,
    language: account.language,
    phone_number: account.phone_number,
    secondary_email: account.secondary_email,
  }
}

async function updateGeneralSettings() {
  const { valid } = await profileForm.value.validate()
  if (!valid) {
    return
  }
  loadingUpdateProfile.value = true
  authStore
    .updateAccount(form.value)
    .then(() => {
      busStore.displayNotification({ msg: $gettext('Profile updated') })
      console.log(authStore.accountLanguage)
      console.log(available)
      if (!(authStore.accountLanguage in available)) {
        languageError.value = $gettext('Language does no exist')
      }
    })
    .finally(() => (loadingUpdateProfile.value = false))
}

async function updatePassword() {
  const { valid } = await passwordForm.value.validate()
  if (!valid) {
    return
  }
  loadingPasswordUpdate.value = true
  authStore
    .updateAccount({ password: form.value.password })
    .then(() => {
      busStore.displayNotification({ msg: $gettext('Password updated') })
    })
    .finally(() => (loadingPasswordUpdate.value = false))
}

onMounted(() => {
  initFormFromAccount(account.value)
  languagesApi.getAll().then((resp) => {
    languages.value = resp.data
  })
})

watch(
  () => account,
  (newValue) => {
    if (newValue) {
      initFormFromAccount(newValue)
    } else {
      form.value = {}
    }
  }
)
</script>
