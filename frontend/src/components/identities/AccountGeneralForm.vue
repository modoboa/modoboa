<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    vid="username"
    >
    <label class="m-label">{{ $gettext('Username') }}</label>
    <email-field
      ref="username"
      v-model="account.username"
      :error-messages="errors"
      :placeholder="usernamePlaceholder"
      :type="usernameInputType"
      outlined
      dense
      />
  </validation-provider>
  <label class="m-label">{{ $gettext('First name') }}</label>
  <v-text-field
    v-model="account.first_name"
    outlined
    dense
    />
  <label class="m-label">{{ $gettext('Last name') }}</label>
  <v-text-field
    v-model="account.last_name"
    outlined
    dense
    />
  <div class="d-flex align-center">
    <v-switch
      v-model="account.random_password"
      :label="'Random password'|translate"
      @change="updatePassword"
      dense
      />
    <template v-if="account.pk && account.random_password">
      <v-alert style="background-color: #515D78" class="ml-6" dense>
        <span class="white--text mr-4">{{ account.password }}</span>
        <v-btn small color="white" icon :title="'Copy to clipboard'|translate" @click="copyPassword">
          <v-icon>mdi-clipboard-multiple-outline</v-icon>
        </v-btn>
      </v-alert>
    </template>
  </div>
  <validation-provider
    v-if="!account.random_password"
    v-slot="{ errors }"
    :rules="passwordRules"
    vid="password"
    >
    <label class="m-label">{{ $gettext('Password') }}</label>
    <v-text-field
      v-model="account.password"
      :error-messages="errors"
      outlined
      type="password"
      dense
      />
  </validation-provider>
  <validation-provider
    v-if="!account.random_password"
    v-slot="{ errors }"
    :rules="passwordConfirmationRules"
    >
    <label class="m-label">{{ $gettext('Confirmation') }}</label>
    <v-text-field
      v-model="account.password_confirmation"
      :error-messages="errors"
      outlined
      type="password"
      dense
      />
  </validation-provider>
  <v-switch
    v-model="account.is_active"
    :label="'Enabled' | translate"
    dense
    />
</validation-observer>
</template>

<script>
import { bus } from '@/main'
import accounts from '@/api/accounts'
import EmailField from '@/components/tools/EmailField'

export default {
  components: {
    EmailField
  },
  props: ['account'],
  computed: {
    passwordRules () {
      return (this.account.pk) ? '' : 'required'
    },
    passwordConfirmationRules () {
      return (this.account.password) ? 'required' : ''
    },
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
    copyPassword () {
      navigator.clipboard.writeText(this.account.password).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Password copied to clipboard') })
      })
    },
    updatePassword (value) {
      if (value) {
        accounts.getRandomPassword().then(resp => {
          this.$set(this.account, 'password', resp.data.password)
        })
      } else {
        this.$set(this.account, 'password', null)
        this.$set(this.account, 'password_confirmation', null)
      }
    }
  },
  mounted () {
    if (this.account.random_password) {
      this.updatePassword(true)
    }
  }
}
</script>
