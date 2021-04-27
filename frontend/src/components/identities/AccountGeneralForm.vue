<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    vid="username"
    >
    <label class="m-label">{{ $gettext('Username') }}</label>
    <email-field
      v-model="account.username"
      :error-messages="errors"
      :placeholder="usernamePlaceholder"
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
  <v-switch
    v-model="account.random_password"
    :label="'Random password' | translate"
    dense
    />
  <validation-provider
    v-if="!account.random_password"
    v-slot="{ errors }"
    rules="required"
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
    rules="required"
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
import EmailField from '@/components/tools/EmailField'

export default {
  components: {
    EmailField
  },
  props: ['account'],
  computed: {
    usernamePlaceholder () {
      if (this.account.role === 'SimpleUsers') {
        return this.$gettext('Enter an email address')
      }
      return this.$gettext('Enter a simple username or an email address')
    }
  },
  data () {
    return {
    }
  },
  methods: {
  },
  mounted () {
  }
}
</script>
