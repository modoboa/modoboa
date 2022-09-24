<template>
<validation-observer ref="observer">
  <validation-provider
    v-slot="{ errors }"
    rules="required"
    >
    <label class="m-label">{{ $gettext('Username') }}</label>
    <email-field
      ref="username"
      v-model="form.username"
      :error-messages="errors"
      :placeholder="usernamePlaceholder"
      :type="usernameInputType"
      @input="update"
      />
  </validation-provider>
  <label class="m-label">{{ $gettext('First name') }}</label>
  <v-text-field
    v-model="form.first_name"
    autocomplete="new-password"
    outlined
    dense
    @input="update"
    />
  <label class="m-label">{{ $gettext('Last name') }}</label>
  <v-text-field
    v-model="form.last_name"
    autocomplete="new-password"
    outlined
    dense
    @input="update"
    />

  <account-password-form
    ref="passwordForm"
    v-model="form.password"
    :account="form"
    @input="update"
    />

  <v-switch
    v-model="form.is_active"
    :label="'Enabled' | translate"
    dense
    @input="update"
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
  props: ['value', 'account'],
  data () {
    return {
      form: {}
    }
  },
  computed: {
    usernamePlaceholder () {
      if (this.form.role === 'SimpleUsers') {
        return this.$gettext('Enter an email address')
      }
      return this.$gettext('Enter a simple username or an email address')
    },
    usernameInputType () {
      return (this.form.role === 'SimpleUsers') ? 'email' : 'text'
    }
  },
  methods: {
    async validateForm () {
      return await this.$refs.observer.validate() && await this.$refs.passwordForm.validate()
    },
    update () {
      console.log(this.form)
      this.$emit('input', this.form)
    }
  },
  mounted () {
    this.form = { ...this.value }
  }
}
</script>
