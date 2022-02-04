<template>
<div>
  <validation-observer ref="observer">

  <validation-provider
    v-if="withPasswordCheck"
    v-slot="{ errors }"
    rules="required|validPassword"
    mode="lazy"
    >
    <label class="m-label">{{ $gettext('Current password') }}</label>
    <v-text-field
      v-model="form.currentPassword"
      :error-messages="errors"
      outlined
      type="password"
      dense
      />
  </validation-provider>
  <div class="d-flex align-center">
    <v-switch
      v-model="form.random_password"
      :label="'Random password'|translate"
      @change="updatePassword"
      dense
      />
    <template v-if="form.random_password">
      <v-alert style="background-color: #515D78" class="ml-6" dense>
        <span class="white--text mr-4">{{ form.password }}</span>
        <v-btn small color="white" icon :title="'Copy to clipboard'|translate" @click="copyPassword">
          <v-icon>mdi-clipboard-multiple-outline</v-icon>
        </v-btn>
      </v-alert>
    </template>
  </div>
  <validation-provider
    v-if="!form.random_password"
    v-slot="{ errors }"
    :rules="passwordRules"
    vid="password"
    >
    <label class="m-label">{{ $gettext('Password') }}</label>
    <v-text-field
      :value="value"
      :error-messages="errors"
      outlined
      type="password"
      dense
      @input="(value) => $emit('input', value)"
      />
  </validation-provider>
  <validation-provider
    v-if="!form.random_password"
    v-slot="{ errors }"
    :rules="passwordConfirmationRules"
    vid="confirmation"
    >
    <label class="m-label">{{ $gettext('Confirmation') }}</label>
    <v-text-field
      v-model="form.password_confirmation"
      :error-messages="errors"
      outlined
      type="password"
      dense
      />
  </validation-provider>
  </validation-observer>
</div>
</template>

<script>
import { bus } from '@/main'
import accounts from '@/api/accounts'

export default {
  props: {
    value: String,
    withPasswordCheck: {
      type: Boolean,
      default: false
    },
    account: {
      type: Object,
      required: false
    }
  },
  data () {
    return {
      form: {}
    }
  },
  computed: {
    passwordRules () {
      return (this.account && this.account.pk) ? '' : 'required'
    },
    passwordConfirmationRules () {
      return (this.value) ? 'required|samePassword:password' : ''
    }
  },
  methods: {
    copyPassword () {
      navigator.clipboard.writeText(this.form.password).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Password copied to clipboard') })
      })
    },
    updatePassword (value) {
      if (value) {
        accounts.getRandomPassword().then(resp => {
          this.$set(this.form, 'password', resp.data.password)
          this.$emit('input', this.form.password)
        })
      } else {
        this.$set(this.form, 'password', null)
        this.$set(this.form, 'password_confirmation', null)
      }
    },
    async validate () {
      return await this.$refs.observer.validate()
    }
  },
  mounted () {
    if (this.account) {
      this.form.random_password = this.account.random_password
      if (this.form.random_password) {
        this.updatePassword(true)
      }
    }
  }
}
</script>
