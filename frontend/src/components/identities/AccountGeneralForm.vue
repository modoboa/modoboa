<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Username') }}</label>
    <email-field
      ref="username"
      v-model="account.username"
      :error-messages="errors"
      :placeholder="usernamePlaceholder"
      :type="usernameInputType"
      />
  </validation-provider>
  <label class="m-label">{{ $gettext('First name') }}</label>
  <v-text-field
    v-model="account.first_name"
    autocomplete="new-password"
    outlined
    dense
    />
  <label class="m-label">{{ $gettext('Last name') }}</label>
  <v-text-field
    v-model="account.last_name"
    autocomplete="new-password"
    outlined
    dense
    />

  <account-password-form
    ref="passwordForm"
    v-model="account.password"
    :account="account"
    />

  <v-switch
    v-model="account.is_active"
    :label="'Enabled' | translate"
    dense
    />
</validation-observer>
</template>

<script>
import AccountPasswordForm from './AccountPasswordForm'
import EmailField from '@/components/tools/EmailField'

export default {
  components: {
    AccountPasswordForm,
    EmailField
  },
  props: ['account'],
  computed: {
    usernamePlaceholder () {
      if (this.account.role === 'SimpleUsers') {
        return this.$gettext('Enter an email address')
      }
      return this.$gettext('Enter a simple username or an email address')
    },
    usernameInputType () {
      return (this.account.role === 'SimpleUsers') ? 'email' : 'text'
    }
  },
  methods: {
    async validateForm () {
      return await this.$refs.observer.validate() && await this.$refs.passwordForm.validate()
    }
  }
}
</script>
