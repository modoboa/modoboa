<template>
<div>
  <v-expansion-panels v-model="panel">
    <v-expansion-panel>
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Role</translate>
          </v-col>
          <v-col
            cols="8"
            class="text--secondary"
            >
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row
                v-else
                no-gutters
                style="width: 100%"
                >
                <v-col cols="6">
                  {{ $refs.roleForm.roleLabel }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <account-role-form ref="roleForm" v-model="editedAccount.role" :account="editedAccount" />
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel>
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Identification</translate>
          </v-col>
          <v-col
            cols="8"
            class="text--secondary"
            >
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row
                v-else
                no-gutters
                style="width: 100%"
                >
                <v-col cols="6">
                  <translate class="mr-2">Username:</translate> {{ editedAccount.username }}
                </v-col>
                <v-col cols="6">
                  <translate class="mr-2">Enabled</translate>
                  <v-icon color="success" v-if="editedAccount.is_active">mdi-check-circle-outline</v-icon>
                  <v-icon v-else>mdi-close-circle-outline</v-icon>
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <account-general-form ref="generalForm" v-model="editedAccount" />
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel v-if="usernameIsEmail">
      <v-expansion-panel-header v-slot="{ open }">
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Mailbox</translate>
          </v-col>
          <v-col
            cols="8"
            class="text--secondary"
            >
            <v-fade-transition leave-absolute>
              <span v-if="open"></span>
              <v-row
                v-else
                no-gutters
                style="width: 100%"
                >
                <template v-if="account.mailbox">
                  <v-col cols="6" v-if="account.mailbox.use_domain_quota">
                    <translate class="mr-2">Quota: </translate> <translate>domain's default value</translate>
                  </v-col>
                  <v-col cols="6" v-else>
                    <translate class="mr-2">Quota: </translate> {{ account.mailbox.quota }}
                  </v-col>
                </template>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <account-mailbox-form ref="mailboxForm" v-model="editedAccount" />
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel
      v-if="limitsConfig.params.enable_admin_limits && account.role !== 'SimpleUsers' && account.role !== 'SuperAdmins'"
      >
      <v-expansion-panel-header>
        <v-row no-gutters>
          <v-col cols="4">
            <translate>Resources</translate>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <resources-form ref="resourcesForm" :resources="editedAccount.resources" />
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
  <div class="mt-4 d-flex justify-end">
    <v-btn @click="$router.go(-1)">
      <translate>Cancel</translate>
    </v-btn>
    <v-btn class="ml-4" color="primary darken-1" @click="save">
      <translate>Save</translate>
    </v-btn>
  </div>
</div>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import { bus } from '@/main'
import accounts from '@/api/accounts'
import AccountGeneralForm from './AccountGeneralForm'
import AccountMailboxForm from './AccountMailboxForm'
import AccountRoleForm from './AccountRoleForm'
import ResourcesForm from '@/components/tools/ResourcesForm'
import parameters from '@/api/parameters'

export default {
  components: {
    AccountGeneralForm,
    AccountMailboxForm,
    AccountRoleForm,
    ResourcesForm
  },
  props: ['account'],
  computed: {
    usernameIsEmail () {
      return this.editedAccount.username && this.editedAccount.username.indexOf('@') !== -1
    }
  },
  data () {
    return {
      editedAccount: {},
      limitsConfig: {},
      panel: 0
    }
  },
  methods: {
    async save () {
      if (this.$refs.generalForm !== undefined) {
        const valid = await this.$refs.generalForm.validateForm()
        if (!valid) {
          return
        }
      }
      if (this.$refs.resourcesForm !== undefined) {
        const valid = await this.$refs.resourcesForm.validateForm()
        if (!valid) {
          return
        }
      }
      try {
        const data = JSON.parse(JSON.stringify(this.editedAccount))
        if (this.usernameIsEmail) {
          data.mailbox.full_address = data.username
        } else {
          delete data.mailbox.full_address
        }
        if (_isEmpty(data.mailbox)) {
          delete data.mailbox
        }
        if (data.random_password || !data.password) {
          delete data.password
          delete data.password_confirmation
        }
        if (this.$refs.resourcesForm !== undefined) {
          data.resources = this.$refs.resourcesForm.getPayload()
        }
        if (data.aliases === null) {
          delete data.aliases
        }
        await accounts.patch(this.editedAccount.pk, data).then(resp => {
          bus.$emit('notification', { msg: this.$gettext('Account updated') })
        })
      } catch (error) {
        if (this.$refs.generalForm) {
          this.$refs.generalForm.$refs.observer.setErrors(error.response.data)
        }
        if (this.$refs.mailboxForm) {
          this.$refs.mailboxForm.$refs.observer.setErrors(error.response.data)
        }
        if (this.$refs.resourcesForm) {
          this.$refs.resourcesForm.$refs.observer.setErrors(error.response.data)
        }
      }
    }
  },
  created () {
    parameters.getApplication('limits').then(resp => {
      this.limitsConfig = resp.data
    })
  },
  mounted () {
    this.$store.dispatch('identities/fetchDomains')
  },
  watch: {
    account: {
      handler: function (val) {
        if (val) {
          this.editedAccount = { ...val }
          delete this.editedAccount.domains
          if (this.editedAccount.mailbox === null) {
            this.editedAccount.mailbox = {}
          }
        }
      },
      immediate: true
    }
  }
}
</script>
