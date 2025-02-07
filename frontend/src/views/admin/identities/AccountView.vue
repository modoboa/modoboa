<template>
  <v-toolbar flat>
    <v-toolbar-title>
      {{ $gettext('Account') }} {{ account.username }}
      <v-btn
        color="primary"
        icon="mdi-circle-edit-outline"
        :to="{ name: 'AccountEdit', params: { id: account.pk } }"
      />
      <v-btn color="primary" icon="mdi-reload" @click="refreshAccount" />
    </v-toolbar-title>
  </v-toolbar>
  <v-row>
    <v-col cols="6">
      <AccountSummary :account="account" />
      <DomainAdminDomains
        v-if="account.role === 'DomainAdmins'"
        class="mt-2"
        :account="account"
      />
    </v-col>
    <v-col cols="6">
      <ResourcesView
        v-if="
          limitsConfig.params &&
          limitsConfig.params.enable_admin_limits &&
          account.role !== 'SimpleUsers' &&
          account.role !== 'SuperAdmins'
        "
        :resources="account.resources"
      />
      <AccountAliases v-if="account.aliases" class="mt-2" :account="account" />
      <AccountSenderAddresses
        v-if="account.mailbox"
        class="mt-2"
        :account="account"
      />
    </v-col>
  </v-row>
</template>

<script setup lang="js">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAccountsStore } from '@/stores'
import parametersApi from '@/api/parameters'
import AccountAliases from '@/components/admin/identities/AccountAliases.vue'
import AccountSenderAddresses from '@/components/admin/identities/AccountSenderAddresses.vue'
import AccountSummary from '@/components/admin/identities/AccountSummary.vue'
import DomainAdminDomains from '@/components/admin/identities/DomainAdminDomains.vue'
import ResourcesView from '@/components/tools/ResourcesView.vue'

const route = useRoute()
const accountsStore = useAccountsStore()

const account = computed(() => {
  if (accountsStore.accounts[route.params.id] !== undefined) {
    return accountsStore.accounts[route.params.id]
  }
  refreshAccount()
  return { pk: route.params.id }
})
const limitsConfig = ref({})

parametersApi.getGlobalApplication('limits').then((resp) => {
  limitsConfig.value = resp.data
})

function refreshAccount() {
  accountsStore.getAccount(route.params.id)
}
</script>

<style scoped>
.v-toolbar {
  background-color: #f7f8fa !important;
}
</style>
