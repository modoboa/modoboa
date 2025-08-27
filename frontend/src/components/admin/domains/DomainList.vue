<template>
  <v-card class="mt-6">
    <v-data-table
      v-model="selected"
      :expanded="expanded"
      :headers="domainHeaders"
      :items="domains"
      item-value="pk"
      :search="search"
      show-select
      expand-on-click
      :loading="loading"
    >
      <template #top>
        <v-toolbar color="white" flat>
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            :placeholder="$gettext('Search')"
            variant="outlined"
            single-line
            hide-details
            density="compact"
            class="flex-grow-0 w-33 mr-4"
          ></v-text-field>
          <slot name="extraActions" />
          <v-menu location="bottom">
            <template #activator="{ props }">
              <v-btn
                variant="flat"
                append-icon="mdi-chevron-down"
                v-bind="props"
                size="small"
              >
                {{ $gettext('Actions') }}
              </v-btn>
            </template>
            <v-list density="compact"> </v-list>
          </v-menu>
          <v-btn
            variant="text"
            icon="mdi-reload"
            @click="reloadDomains"
          ></v-btn>
        </v-toolbar>
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'DomainDetail',
            params: { id: item.pk },
          }"
        >
          {{ item.name }}
        </router-link>
        <v-chip
          v-if="item.type === 'relaydomain'"
          size="small"
          color="primary"
          class="ml-2"
        >
          {{ $gettext('Relay') }}
        </v-chip>
      </template>

      <template #[`item.enabled`]="{ item }">
        <BooleanIcon :value="item.enabled" />
      </template>

      <template
        #[`item.data-table-expand`]="{
          item,
          internalItem,
          isExpanded,
          toggleExpand,
        }"
      >
        {{ item.domainalias_count }} aliases
        <v-btn
          v-if="item.domainalias_count"
          variant="text"
          size="small"
          :icon="
            isExpanded(internalItem) ? 'mdi-chevron-up' : 'mdi-chevron-down'
          "
          @click="loadAliases(item, internalItem, isExpanded, toggleExpand)"
        >
        </v-btn>
      </template>

      <template #[`item.dns_global_status`]="{ item }">
        <DNSStatusChip :status="item.dns_global_status" />
      </template>

      <template #[`item.message_limit`]="{ item }">
        <v-progress-linear
          v-if="item.message_limit"
          :color="item.sent_messages_in_percent < 80 ? 'primary' : 'warning'"
          :model-value="item.sent_messages_in_percent"
        />
        <span v-else>
          {{ $gettext('Unlimited') }}
        </span>
      </template>

      <template #[`item.allocated_quota_in_percent`]="{ item }">
        <v-progress-linear
          v-if="item.quota !== '0'"
          :color="item.allocated_quota_in_percent < 80 ? 'primary' : 'warning'"
          :model-value="item.allocated_quota_in_percent"
        />
        <span v-else>
          {{ $gettext('Unlimited') }}
        </span>
      </template>

      <template #[`item.actions`]="{ item }">
        <div class="text-right">
          <v-menu offset-y>
            <template #activator="{ props }">
              <v-badge
                v-if="item.opened_alarms_count"
                bordered
                color="error"
                icon="mdi-bell"
                overlap
              >
                <v-btn icon="mdi-dots-horizontal" variant="text" v-bind="props">
                </v-btn>
              </v-badge>
              <v-btn
                v-else
                icon="mdi-dots-horizontal"
                variant="text"
                v-bind="props"
              >
              </v-btn>
            </template>
            <MenuItems :items="getDomainMenuItems(item)" :obj="item" />
          </v-menu>
        </div>
      </template>

      <template #expanded-row="{ item, columns }">
        <tr class="grey lighten-4">
          <td :colspan="columns.length">
            <span
              v-for="alias in aliases[item.name]"
              :key="alias.name"
              class="mr-4"
            >
              <v-chip class="mr-2" @click="editDomainAlias(item, alias)">
                {{ alias.name }}
              </v-chip>
            </span>
          </td>
        </tr>
      </template>
    </v-data-table>
    <ConfirmDialog ref="confirm">
      <v-checkbox
        v-model="keepDomainFolder"
        :label="$gettext('Do not delete domain folder')"
        hide-details
      />
    </ConfirmDialog>
    <v-dialog v-model="showAliasForm" persistent max-width="800px">
      <DomainAliasForm
        :domain-alias="selectedDomainAlias"
        @close="closeDomainAliasForm"
      />
    </v-dialog>
    <v-dialog v-model="showAdminList" persistent max-width="800px">
      <DomainAdminList
        :domain="selectedDomain"
        dialog-mode
        @close="showAdminList = false"
      />
    </v-dialog>
  </v-card>
</template>

<script setup lang="js">
import { useBusStore } from '@/stores'
import { useGettext } from 'vue3-gettext'
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/permissions'
import BooleanIcon from '@/components/tools/BooleanIcon.vue'
import DomainAdminList from './DomainAdminList.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import DNSStatusChip from './DNSStatusChip.vue'
import DomainAliasForm from './DomainAliasForm.vue'
import MenuItems from '@/components/tools/MenuItems.vue'
import domainsApi from '@/api/domains'

import { ref, onMounted } from 'vue'

const { $gettext } = useGettext()
const router = useRouter()

const { canSetRole } = usePermissions()
const busStore = useBusStore()

const domainHeaders = [
  { title: $gettext('Name'), key: 'name' },
  { title: $gettext('Enabled'), key: 'enabled', width: '5%' },
  { title: $gettext('Aliases'), key: 'data-table-expand', width: '10%' },
  {
    title: $gettext('DNS status'),
    key: 'dns_global_status',
    sortable: false,
  },
  { title: $gettext('Sending limit'), key: 'message_limit' },
  { title: $gettext('Quota'), key: 'allocated_quota_in_percent' },
]

if (canSetRole.value) {
  domainHeaders.push({
    title: $gettext('Actions'),
    value: 'actions',
    sortable: false,
    align: 'end',
  })
}

const aliases = ref({})
const confirm = ref()
const domains = ref([])
const keepDomainFolder = ref(false)
const loading = ref(false)
const selectedDomain = ref(null)
const selectedDomainAlias = ref(null)
const showAdminList = ref(false)
const showAliasForm = ref(false)
const search = ref('')
const selected = ref([])
const expanded = ref([])

async function reloadDomains() {
  aliases.value = {}
  loading.value = true
  try {
    const resp = await domainsApi.getDomains()
    domains.value = resp.data
  } finally {
    loading.value = false
  }
}

function closeDomainAliasForm() {
  showAliasForm.value = false
  selectedDomain.value = null
  selectedDomainAlias.value = null
}

async function deleteDomain(domain) {
  const result = await confirm.value.open(
    $gettext('Warning'),
    $gettext('Do you really want to delete the domain %{ domain }?', {
      domain: domain.name,
    }),
    {
      color: 'error',
      cancelLabel: $gettext('No'),
      agreeLabel: $gettext('Yes'),
    }
  )
  if (!result) {
    return
  }
  loading.value = true
  try {
    const data = { keep_folder: keepDomainFolder.value }
    await domainsApi.deleteDomain(domain.pk, data)
    reloadDomains()
    busStore.displayNotification({ msg: $gettext('Domain deleted') })
    keepDomainFolder.value = false
  } finally {
    loading.value = false
  }
}

function editDomain(domain) {
  router.push({ name: 'DomainEdit', params: { id: domain.pk } })
}

function editDomainAlias(domain, alias) {
  selectedDomain.value = domain
  selectedDomainAlias.value = alias
  showAliasForm.value = true
}

async function loadAliases(item, internalItem, isItemExpanded, toggleExpand) {
  const isExpanded = isItemExpanded(internalItem)
  if (!isExpanded) {
    const resp = await domainsApi.getDomainAliases(item.name)
    aliases.value[item.name] = resp.data
  }
}

function openAdminList(domain) {
  selectedDomain.value = domain
  showAdminList.value = true
}

function getDomainMenuItems(domain) {
  const result = [
    {
      label: $gettext('Administrators'),
      icon: 'mdi-account-supervisor',
      onClick: openAdminList,
    },
    {
      label: $gettext('Edit'),
      icon: 'mdi-circle-edit-outline',
      onClick: editDomain,
    },
    {
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteDomain,
      color: 'red',
    },
  ]
  if (domain.opened_alarms_count) {
    result.push({
      label: $gettext('Alarms'),
      icon: 'mdi-bell',
      color: 'red',
      onClick: () => router.push({ name: 'Alarms' }),
    })
  }
  return result
}

onMounted(() => {
  reloadDomains()
})

defineExpose({
  reloadDomains,
})
</script>

<style scoped lang="scss">
.v-text-field--outlined :deep(fieldset) {
  border-color: #bfc5d2;
}
.v-input--checkbox :deep(.v-label) {
  font-size: 0.875rem !important;
}

a {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));

  &:visited {
    color: rgb(var(--v-theme-primary));
  }
}
</style>
