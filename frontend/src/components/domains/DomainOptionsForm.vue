<template>
<validation-observer ref="observer">
  <v-switch v-model="createAdmin"
            :label="'Create a domain administrator' | translate"
            @change="update"
            />
  <validation-provider
    v-slot="{ errors }"
    :rules="(createAdmin) ? 'required' : ''"
    >
    <v-text-field
      :label="'Name' | translate"
      :hint="'Name of the administrator' | translate"
      persistent-hint
      v-model="domain.domain_admin.username"
      :error-messages="errors"
      outlined
      :disabled="!createAdmin"
      :suffix="`@${domain.name}`"
      />
  </validation-provider>
  <v-switch v-model="domain.domain_admin.with_random_password"
            :label="'Random password' | translate"
            :disabled="!createAdmin"
            :hint="'Generate a random password for the administrator.' | translate"
            @change="updatePassword"
            persistent-hint
            />
  <v-switch v-model="domain.domain_admin.with_mailbox"
            :label="'With a mailbox' | translate"
            :disabled="!createAdmin"
            :hint="'Create a mailbox for the administrator.' | translate"
            persistent-hint
            />
  <v-switch v-model="domain.domain_admin.with_aliases"
            :label="'Create aliases' | translate"
            :disabled="!createAdmin"
            :hint="'Create standard aliases for the domain.' | translate"
            persistent-hint
            />
</validation-observer>
</template>

<script>
import accounts from '@/api/accounts'

export default {
  props: ['domain'],
  data () {
    return {
      createAdmin: false
    }
  },
  methods: {
    updatePassword (value) {
      if (value) {
        accounts.getRandomPassword().then(resp => {
          this.$set(this.domain.domain_admin, 'password', resp.data.password)
        })
      } else {
        delete this.domain.domain_admin.password
      }
    },

    update (val) {
      this.$emit('createAdmin', val)
    }
  }
}
</script>
