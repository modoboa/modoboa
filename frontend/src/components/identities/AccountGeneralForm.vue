<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <choice-field v-model="account.role"
                  :label="'Role' | translate"
                  :choices="accountRoles"
                  :error-messages="errors"
                  />
  </validation-provider>
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-text-field
      v-model="account.username"
      :label="'Username' | translate"
      :error-messages="errors"
      outlined
      class="mt-4"
      dense
      />
  </validation-provider>
  <v-text-field
    v-model="account.first_name"
    :label="'First name' | translate"
    outlined
    dense
    />
  <v-text-field
    v-model="account.last_name"
    :label="'Last name' | translate"
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
    >
    <v-text-field
      v-model="account.password"
      :label="'Password' | translate"
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
    <v-text-field
      v-model="account.password_confirmation"
      :label="'Confirmation' | translate"
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
import ChoiceField from '@/components/tools/ChoiceField'

export default {
  components: {
    ChoiceField
  },
  props: ['account'],
  data () {
    return {
      accountRoles: [
        {
          label: this.$gettext('Domain administrator'),
          value: 'DomainAdmins'
        },
        {
          label: this.$gettext('Reseller'),
          value: 'Resellers'
        },
        {
          label: this.$gettext('Simple user'),
          value: 'SimpleUsers'
        },
        {
          label: this.$gettext('Super administrator'),
          value: 'SuperAdmins'
        }
      ]
    }
  }
}
</script>
