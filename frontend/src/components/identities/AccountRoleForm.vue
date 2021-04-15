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
                  :choices-per-line="2"
                  />
  </validation-provider>
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
