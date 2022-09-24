<template>
<validation-observer ref="observer">
  <v-switch v-model="createAdmin"
            :label="'Create a domain administrator' | translate"
            @change="updateCreateAdmin"
            />
  <validation-provider
    v-slot="{ errors }"
    :rules="(createAdmin) ? 'required' : ''"
    >
    <v-text-field
      :label="'Name' | translate"
      :hint="'Name of the administrator' | translate"
      persistent-hint
      v-model="form.domain_admin.username"
      :error-messages="errors"
      outlined
      :disabled="!createAdmin"
      :suffix="`@${value.name}`"
      @input="update"
      />
  </validation-provider>
  <v-switch v-model="form.domain_admin.with_random_password"
            :label="'Random password' | translate"
            :disabled="!createAdmin"
            :hint="'Generate a random password for the administrator.' | translate"
            @change="updatePassword"
            persistent-hint
            @input="update"
            />
  <v-switch v-model="form.domain_admin.with_mailbox"
            :label="'With a mailbox' | translate"
            :disabled="!createAdmin"
            :hint="'Create a mailbox for the administrator.' | translate"
            persistent-hint
            @input="update"
            />
  <v-switch v-model="form.domain_admin.with_aliases"
            :label="'Create aliases' | translate"
            :disabled="!createAdmin"
            :hint="'Create standard aliases for the domain.' | translate"
            persistent-hint
            @input="update"
            />
</validation-observer>
</template>

<script>
import accounts from '@/api/accounts'

export default {
  props: ['value'],
  data () {
    return {
      createAdmin: false,
      form: {}
    }
  },
  methods: {
    updatePassword (value) {
      if (value) {
        accounts.getRandomPassword().then(resp => {
          this.$set(this.form.domain_admin, 'password', resp.data.password)
          this.update()
        })
      } else {
        delete this.form.domain_admin.password
        this.update()
      }
    },
    updateCreateAdmin (val) {
      this.$emit('createAdmin', val)
    },
    update () {
      this.$emit('input', this.form)
    }
  },
  watch: {
    value: {
      handler: function (newValue) {
        this.form = { ...this.value }
      },
      immediate: true
    }
  }
}
</script>
