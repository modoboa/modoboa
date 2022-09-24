<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <v-row>
      <v-col cols="7">
        <choice-field
          :value="account.role"
          :label="'Choose a role' | translate"
          :choices="accountRoles"
          :error-messages="errors"
          :choices-per-line="2"
          @input="value => $emit('input', value)"
          />
      </v-col>
      <v-col cols="5">
        <v-alert text color="primary" class="mt-11 ml-4 rounded-lg">
          <h3 class="headline">{{ roleLabel }}</h3>
          <p class="mt-4">{{ roleHelp }}</p>
          <v-icon color="white" class="float-right" large>mdi-help-circle-outline</v-icon>
        </v-alert>
      </v-col>
    </v-row>
  </validation-provider>
</validation-observer>
</template>

<script>
import ChoiceField from '@/components/tools/ChoiceField'

export default {
  components: {
    ChoiceField
  },
  props: ['value', 'account'],
  computed: {
    roleLabel () {
      const role = this.accountRoles.find(role => role.value === this.account.role)
      return role !== undefined ? role.label : ''
    },
    roleHelp () {
      const role = this.accountRoles.find(role => role.value === this.account.role)
      return role !== undefined ? role.help : ''
    }
  },
  data () {
    return {
      accountRoles: [
        {
          label: this.$gettext('Domain administrator'),
          value: 'DomainAdmins',
          help: this.$gettext('A user with privileges on one or more domain. He will be allowed to administer mailboxes and he can also have a mailbox.')
        },
        {
          label: this.$gettext('Reseller'),
          value: 'Resellers',
          help: this.$gettext('help')
        },
        {
          label: this.$gettext('Simple user'),
          value: 'SimpleUsers',
          help: this.$gettext('A user with no privileges but with a mailbox. He will be allowed to use all end-user features: webmail, calendar, contacts, filters.')
        },
        {
          label: this.$gettext('Super administrator'),
          value: 'SuperAdmins',
          help: this.$gettext('A user with all privileges, can do anything. By default, such a user does not have a mailbox so he can\'t access end-user features.')
        }
      ]
    }
  }
}
</script>
