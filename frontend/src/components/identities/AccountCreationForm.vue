<template>
<div class="d-flex justify-center inner">
  <v-stepper v-model="step">
    <v-stepper-header class="align-center px-10">
      <v-img
        src="../../assets/Modoboa_RVB-BLEU-SANS.png"
        max-width="190"
        />
      <v-stepper-step :complete="step > 1" step="1">
        <translate>Role</translate>
      </v-stepper-step>
      <v-stepper-step :complete="step > 2" step="2">
        <translate>Identification</translate>
      </v-stepper-step>
      <v-stepper-step :complete="step > 3" step="3">
        <translate>Mailbox</translate>
      </v-stepper-step>
      <v-stepper-step :complete="step > 4" step="4">
        <translate>Aliases</translate>
      </v-stepper-step>
      <v-stepper-step step="5">
        <translate>Summary</translate>
      </v-stepper-step>
      <v-btn icon @click="close">
        <v-icon color="primary" x-large>mdi-close</v-icon>
      </v-btn>
    </v-stepper-header>
    <v-stepper-items class="mt-4 d-flex justify-center">
      <v-stepper-content step="1" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New account</translate> /
          <translate>Role</translate>
        </div>
        <account-role-form ref="form_1" :account="account" />
        <div class="d-flex justify-end mt-4">
          <v-btn
            color="primary"
            @click="goToNextStep(1, 2)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="2" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New account</translate> /
          <translate>Identification</translate>
        </div>
        <account-general-form v-if="step >= 2" ref="form_2" :account="account" />
        <div class="d-flex justify-end">
          <v-btn @click="step = 1" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(2, 3)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="3" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New account</translate> /
          <translate>Mailbox</translate>
        </div>
        <account-mailbox-form ref="form_3" :account="account" />
        <div class="d-flex justify-end">
          <v-btn @click="step = 2" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(3, 4)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="4" class="flex-grow-0">
        <div class="mb-6 text-h5">
          <translate class="grey--text text--darken-1">New account</translate> /
          <translate>Aliases</translate>
        </div>
        <account-alias-form v-if="step >= 4" ref="form_4" :account="account" />
        <div class="d-flex justify-end">
          <v-btn @click="step = 3" class="mr-10" text>
            <translate>Back</translate>
          </v-btn>
          <v-btn
            color="primary"
            @click="goToNextStep(4, 5)"
            large
            >
            <translate>Next</translate>
          </v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="5" class="flex-grow-0">
        <div class="text-center text-h3"><translate>Summary</translate></div>
        <creation-summary
          :sections="summarySections"
          @modify-step="val => step = val"
          >
          <template v-slot:item.random_password="{ item }">
            <v-col cols="12" class="highligth white--text">
              <v-row>
                <v-col><span>{{ item.key }}</span></v-col>
                <v-col class="text-right" v-if="item.type === 'yesno'">
                  {{ item.value|yesno }}
                </v-col>
              </v-row>
              <v-row>
                <v-col class="text-right py-1">
                  {{ account.password }}
                  <v-btn icon color="white" :title="'Copy to clipboard'|translate" @click="copyPassword">
                    <v-icon>mdi-clipboard-multiple-outline</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </v-col>
          </template>
        </creation-summary>
        <div class="d-flex justify-center mt-8">
          <v-btn
            color="primary"
            @click="submit"
            large
            >
            <translate>Confirm and create</translate>
          </v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
  <confirm-dialog ref="confirm" />
</div>
</template>

<script>
import { bus } from '@/main'
import accounts from '@/api/accounts'
import AccountAliasForm from './AccountAliasForm'
import AccountGeneralForm from './AccountGeneralForm'
import AccountMailboxForm from './AccountMailboxForm'
import AccountRoleForm from './AccountRoleForm'
import ConfirmDialog from '@/components/layout/ConfirmDialog'
import CreationSummary from '@/components/tools/CreationSummary'

export default {
  components: {
    AccountAliasForm,
    AccountGeneralForm,
    AccountMailboxForm,
    AccountRoleForm,
    ConfirmDialog,
    CreationSummary
  },
  computed: {
    summarySections () {
      const result = [
        {
          title: this.$gettext('Role'),
          items: [
            { key: this.$gettext('Role'), value: this.account.role }
          ]
        },
        {
          title: this.$gettext('Identification'),
          items: [
            { key: this.$gettext('Username'), value: this.account.username },
            { key: this.$gettext('First name'), value: this.account.first_name },
            { key: this.$gettext('Last name'), value: this.account.last_name },
            {
              name: 'random_password',
              key: this.$gettext('Random password'),
              value: this.account.random_password,
              type: 'yesno'
            },
            {
              key: this.$gettext('Enabled'),
              value: this.account.is_active,
              type: 'yesno'
            }
          ]
        },
        {
          title: this.$gettext('Mailbox'),
          items: [
            { key: this.$gettext('Email'), value: this.account.mailbox.full_address },
            {
              key: this.$gettext('Quota'),
              value: (this.account.mailbox.use_domain_quota)
                ? this.$gettext('Domain default value')
                : this.account.mailbox.quota
            },
            {
              key: this.$gettext('Message sending limit'),
              value: this.account.mailbox.message_limit
            }
          ]
        },
        {
          title: this.$gettext('Aliases'),
          items: [
            {
              key: this.$gettext('Aliases'),
              value: this.account.aliases,
              type: 'list'
            }
          ]
        }
      ]
      return result
    }
  },
  data () {
    return {
      account: this.getInitialForm(),
      step: 1
    }
  },
  methods: {
    copyPassword () {
      navigator.clipboard.writeText(this.account.password).then(() => {
        bus.$emit('notification', { msg: this.$gettext('Password copied to clipboard') })
      })
    },
    getInitialForm () {
      return {
        aliases: [],
        is_active: true,
        role: 'SimpleUsers',
        mailbox: {
          use_domain_quota: true
        },
        random_password: true
      }
    },
    async close (withConfirm) {
      if (withConfirm) {
        const confirm = await this.$refs.confirm.open(
          this.$gettext('Warning'),
          this.$gettext('If you close this form now, your modifications won\'t be saved. Do you confirm?'),
          {
            color: 'error'
          }
        )
        if (!confirm) {
          return
        }
      }
      this.account = this.getInitialForm()
      this.$emit('close')
      this.step = 1
    },
    async goToNextStep (current, next) {
      const valid = await this.$refs[`form_${current}`].$refs.observer.validate()
      if (!valid) {
        return
      }
      try {
        await accounts.validate(this.account)
      } catch (error) {
        if (error.response.data.mailbox && error.response.data.mailbox.full_address) {
          this.$refs[`form_${current}`].$refs.observer.setErrors({
            username: error.response.data.mailbox.full_address
          })
        }
        this.$refs[`form_${current}`].$refs.observer.setErrors(error.response.data)
        return
      }
      this.step = next
    },
    submit () {
      accounts.create(this.account).then(resp => {
        bus.$emit('notification', { msg: this.$gettext('Account created') })
        this.$emit('created')
        this.close()
      })
    }
  },
  mounted () {
    this.$store.dispatch('identities/fetchDomains')
  }
}
</script>

<style lang="scss">
.inner {
  background-color: #fff;
}
.v-stepper {
  width: 100%;
  overflow: auto;

  &__content {
    width: 60%;
  }

  &__items {
    overflow-y: auto;
  }

  &__wrapper {
    padding: 0 10px;
  }
}
.subtitle {
  color: #000;
  border-bottom: 1px solid #DBDDDF;
}

.edit-link {
  text-decoration: none;
}
.highligth {
  background-color: #515D78;
}
</style>
