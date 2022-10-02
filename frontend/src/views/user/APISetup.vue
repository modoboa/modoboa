<template>
<div>
  <v-toolbar flat>
    <v-toolbar-title><translate>API access</translate></v-toolbar-title>
  </v-toolbar>
  <div class="pa-4">
    <v-card v-if="!token" flat>
      <v-card-text>
        <translate>Your API token has not been generated yet.</translate>
      </v-card-text>
      <v-card-actions>
        <v-btn
          color="success"
          :loading="loading"
          @click="generateKey"
          >
          <translate>Generate</translate>
        </v-btn>
      </v-card-actions>
    </v-card>
    <v-card v-else flat>
      <v-card-text>
        <label class="m-label"><translate>Your API token is:</translate></label>
        {{ token }}
        <v-btn icon @click="copyToClipboard()" :title="'Copy token to clipboard'|translate">
          <v-icon>mdi-clipboard-plus</v-icon>
        </v-btn>
        <v-btn icon @click="deleteToken()" color="error" :title="'Delete token'|translate">
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </v-card-text>
    </v-card>
    <v-alert type="info" colored-border border="left" class="mt-4">
      <translate>A documentation of the API is available</translate> <a :href="apiDocUrl" target="_blank">here</a>.
    </v-alert>
  </div>
  <confirm-dialog ref="confirm" />
</div>
</template>

<script>
import account from '@/api/account'
import { bus } from '@/main'
import ConfirmDialog from '@/components/layout/ConfirmDialog'

export default {
  components: {
    ConfirmDialog
  },
  computed: {
    apiDocUrl () {
      return this.$config.API_DOC_URL
    }
  },
  data () {
    return {
      loading: false,
      token: null
    }
  },
  methods: {
    copyToClipboard () {
      navigator.clipboard.writeText(this.token)
      bus.$emit('notification', {
        msg: this.$gettext('API token copied to your clipboard'),
        type: 'success'
      })
    },
    generateKey () {
      account.createAPIToken().then(resp => {
        this.token = resp.data.token
        this.loading = false
        bus.$emit('notification', {
          msg: this.$gettext('API token created'),
          type: 'success'
        })
      })
    },
    async deleteToken () {
      const confirm = await this.$refs.confirm.open(
        this.$gettext('Warning'),
        this.$gettext(
          'You are about to delete your API access token'
        ),
        {
          color: 'error',
          cancelLabel: this.$gettext('Cancel'),
          agreeLabel: this.$gettext('Proceed')
        }
      )
      if (!confirm) {
        return
      }
      await account.deleteAPIToken()
      bus.$emit('notification', {
        msg: this.$gettext('API token deleted'),
        type: 'success'
      })
      this.token = null
    }
  },
  mounted () {
    account.getAPIToken().then(resp => {
      this.token = resp.data.token
    })
  }
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
