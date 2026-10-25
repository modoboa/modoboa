<template>
  <v-toolbar flat color="transparent">
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
  <!-- Without plugin tabs, the general content is displayed alone -->
  <v-tabs v-if="pluginTabs.length" v-model="tab" class="mb-4" color="primary">
    <v-tab>
      {{ $gettext('General') }}
    </v-tab>
    <v-tab v-for="extraTab in pluginTabs" :key="extraTab.name">
      {{ extraTab.title }}
    </v-tab>
  </v-tabs>
  <v-tabs-window v-model="tab">
    <v-tabs-window-item>
      <v-row>
        <v-col cols="6">
          <AccountSummary :account="account" />
          <DomainAdminDomains
            v-if="account.role === constants.DOMAIN_ADMIN"
            class="mt-2"
            :account="account"
          />
        </v-col>
        <v-col cols="6">
          <ResourcesView
            v-if="
              limitsConfig.params &&
              limitsConfig.params.enable_admin_limits &&
              account.role !== constants.USER &&
              account.role !== constants.SUPER_ADMIN
            "
            :resources="account.resources"
          />
          <AccountAliases
            v-if="account.aliases"
            class="mt-2"
            :account="account"
          />
          <AccountSenderAddresses
            v-if="account.mailbox"
            class="mt-2"
            :account="account"
          />
        </v-col>
      </v-row>
    </v-tabs-window-item>
    <v-tabs-window-item v-for="extraTab in pluginTabs" :key="extraTab.name">
      <component
        :is="extraTab.component"
        :account="account"
        v-bind="extraTab.props || {}"
        @refresh="refreshAccount"
      />
    </v-tabs-window-item>
  </v-tabs-window>
</template>

<script setup lang="js">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePermissions } from '@/composables/permissions'
import { usePluginsStore } from '@/stores'
import accountsApi from '@/api/accounts'
import parametersApi from '@/api/parameters'
import AccountAliases from '@/components/admin/identities/AccountAliases.vue'
import AccountSenderAddresses from '@/components/admin/identities/AccountSenderAddresses.vue'
import AccountSummary from '@/components/admin/identities/AccountSummary.vue'
import DomainAdminDomains from '@/components/admin/identities/DomainAdminDomains.vue'
import ResourcesView from '@/components/tools/ResourcesView.vue'
import constants from '@/constants.json'

const route = useRoute()
const { canSetRole } = usePermissions()
const pluginsStore = usePluginsStore()

const PLUGIN_TABS_EXTENSION_POINT = 'account.detail.tabs'

const account = ref({ pk: route.params.id })
const limitsConfig = ref({})
const tab = ref(null)

const pluginTabs = computed(() =>
  pluginsStore.uiExtensions(PLUGIN_TABS_EXTENSION_POINT)
)

function refreshAccount() {
  accountsApi.get(route.params.id).then((resp) => {
    account.value = resp.data
  })
}

if (canSetRole.value) {
  parametersApi.getGlobalApplication('limits').then((resp) => {
    limitsConfig.value = resp.data
  })
}

refreshAccount()
</script>
