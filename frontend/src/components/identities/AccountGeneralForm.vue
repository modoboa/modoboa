<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    vid="username"
    >
    <email-field
      v-model="account.username"
      :label="'Username' | translate"
      :error-messages="errors"
      outlined
      class="mt-4"
      />
  </validation-provider>
  <v-text-field
    v-model="account.first_name"
    :label="'First name' | translate"
    outlined
    />
  <v-text-field
    v-model="account.last_name"
    :label="'Last name' | translate"
    outlined
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
    >
    <v-text-field
      v-model="account.password"
      :label="'Password' | translate"
      :error-messages="errors"
      outlined
      type="password"
      />
  </validation-provider>
  <validation-provider
    v-if="!account.random_password"
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      v-model="account.password_confirmation"
      :label="'Confirmation' | translate"
      :error-messages="errors"
      outlined
      type="password"
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
