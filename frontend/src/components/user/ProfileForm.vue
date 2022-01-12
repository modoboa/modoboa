<template>
<v-expansion-panels
  v-model="panel"
  flat
  >
  <v-expansion-panel>
    <v-expansion-panel-header><translate>General settings</translate></v-expansion-panel-header>
    <v-expansion-panel-content>
      <label class="m-label">{{ $gettext('First name') }}</label>
      <v-text-field
        v-model="form.first_name"
        outlined
        dense
        />
      <label class="m-label">{{ $gettext('Last name') }}</label>
      <v-text-field
        v-model="form.last_name"
        outlined
        dense
        />
      <label class="m-label">{{ $gettext('Language') }}</label>
      <v-autocomplete
        v-model="form.language"
        :items="languages"
        item-text="label"
        item-value="code"
        outlined
        dense
        />
      <label class="m-label">{{ $gettext('Phone number') }}</label>
      <v-text-field
        v-model="form.phone_number"
        :label="'Phone number' | translate"
        outlined
        dense
        />
      <label class="m-label">{{ $gettext('Secondary email') }}</label>
      <v-text-field
        v-model="form.secondary_email"
        outlined
        dense
        />
      <v-btn
        color="success"
        @click="updateGeneralSettings"
        >
        <translate>Update settings</translate>
      </v-btn>
    </v-expansion-panel-content>
  </v-expansion-panel>
  <v-expansion-panel>
    <v-expansion-panel-header><translate>Password</translate></v-expansion-panel-header>
    <v-expansion-panel-content>
      <account-password-form
        ref="passwordForm"
        v-model="password"
        with-password-check
        />
      <v-btn
        color="success"
        @click="updatePassword"
        >
        <translate>Update Password</translate>
      </v-btn>
    </v-expansion-panel-content>
  </v-expansion-panel>
</v-expansion-panels>
</template>

<script>
import accounts from '@/api/accounts'
import { bus } from '@/main'
import languages from '@/api/languages'
import AccountPasswordForm from '@/components/identities/AccountPasswordForm'

export default {
  props: {
    account: Object
  },
  components: {
    AccountPasswordForm
  },
  data () {
    return {
      form: {},
      languages: [],
      panel: 0,
      password: null
    }
  },
  methods: {
    initFormFromAccount (account) {
      this.form = {
        first_name: account.first_name,
        last_name: account.last_name,
        language: account.language,
        phone_number: account.phone_number,
        secondary_email: account.secondary_email
      }
    },
    updateGeneralSettings () {
      accounts.patch(this.account.pk, this.form).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Profile updated') })
      })
    },
    async updatePassword () {
      const valid = await this.$refs.passwordForm.validate()
      if (!valid) {
        return
      }
      accounts.patch(this.account.pk, { password: this.password }).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Password updated') })
        this.$refs.passwordObserver.reset()
      })
    }
  },
  mounted () {
    console.log('profile')
    this.initFormFromAccount(this.account)
    languages.getAll().then(resp => {
      this.languages = resp.data
    })
  },
  watch: {
    account (value) {
      if (value) {
        this.initFormFromAccount(value)
      } else {
        this.form = {}
      }
    }
  }
}
</script>
