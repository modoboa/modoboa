<template>
  <v-card class="mt-6">
    <v-data-table-server
      v-model="selected"
      :headers="headers"
      :items="identities"
      :search="search"
      :loading="loading"
      :items-length="totalIdentities"
      :page="currentPage"
      :items-per-page="itemsPerPageR"
      :items-per-page-options="itemsPerPageOptions"
      item-value="pk"
      elevation="0"
      show-select
      :sort-by="sortByR"
      @update:options="updatedOptions"
    >
      <template #top>
        <v-toolbar flat color="white">
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            :placeholder="$gettext('Search')"
            variant="outlined"
            hide-details
            single-line
            flat
            density="compact"
            class="flex-grow-0 w-33 mr-4"
          ></v-text-field>
          <slot name="extraActions" />
          <v-btn
            variant="text"
            icon="mdi-format-columns"
            :title="$gettext('Customize displayed columns')"
            @click="showColumnsForm = true"
          ></v-btn>
          <v-menu v-if="selected.length > 1" location="bottom">
            <template #activator="{ props }">
              <v-btn
                append-icon="mdi-chevron-down"
                v-bind="props"
                size="small"
                variant="flat"
              >
                {{ $gettext('Actions') }}
              </v-btn>
            </template>
            <v-list density="compact">
              <MenuItems :items="getActionMenuItems()" />
            </v-list>
          </v-menu>
          <v-btn
            variant="text"
            icon="mdi-reload"
            @click="fetchIdentities"
          ></v-btn>

          <template #extension>
            <v-radio-group
              v-model="identityType"
              inline
              :readonly="loading"
              hide-details
              @update:model-value="updateType"
            >
              <v-radio
                color="primary"
                :label="$gettext('Accounts')"
                value="account"
              ></v-radio>
              <v-radio
                color="primary"
                :label="$gettext('Alias')"
                value="alias"
              ></v-radio>
            </v-radio-group>
          </template>
        </v-toolbar>
      </template>
      <template #[`item.username`]="{ item }">
        <router-link :to="{ name: 'AccountDetail', params: { id: item.pk } }">
          {{ item.username }}
        </router-link>
      </template>
      <template #[`item.address`]="{ item }">
        <router-link :to="{ name: 'AliasDetail', params: { id: item.pk } }">
          {{ item.address }}
        </router-link>
      </template>
      <template #[`item.is_active`]="{ item }">
        <v-icon
          :color="item.is_active ? 'success' : 'error'"
          :icon="item.is_active ? 'mdi-check-circle' : 'mdi-close-circle'"
          variant="flat"
        />
      </template>
      <template #[`item.enabled`]="{ item }">
        <v-icon
          :color="item.enabled ? 'success' : 'error'"
          :icon="item.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"
          variant="flat"
        />
      </template>
      <template #[`item.recipients`]="{ item }">
        {{ displayRecipients(item) }}
      </template>
      <template #[`item.date_joined`]="{ item }">
        {{ $date(item.date_joined) }}
      </template>
      <template #[`item.creation`]="{ item }">
        {{ $date(item.creation) }}
      </template>
      <template #[`item.last_modification`]="{ item }">
        {{ $date(item.last_modification) }}
      </template>
      <template #[`item.last_login`]="{ item }">
        {{ $date(item.last_login) }}
      </template>
      <template #[`item.role`]="{ item }">
        <v-chip color="default" size="small">
          {{ item.role }}
        </v-chip>
      </template>
      <template #[`item.quota_usage`]="{ item }">
        <template v-if="item.mailbox">
          <v-progress-linear
            v-if="item.mailbox.quota !== '0'"
            :color="item.mailbox.quota_usage < 80 ? 'primary' : 'warning'"
            :model-value="item.mailbox.quota_usage"
          />
          <span v-else>
            {{ $gettext('Unlimited') }}
          </span>
        </template>
        <template v-else>
          {{ $gettext('No mailbox') }}
        </template>
      </template>
      <template #[`item.sent_messages_in_percent`]="{ item }">
        <template v-if="item.mailbox">
          <template
            v-if="
              item.mailbox.message_limit !== null &&
              item.mailbox.message_limit !== undefined
            "
          >
            <v-progress-linear
              v-if="item.mailbox.message_limit !== 0"
              :color="
                item.mailbox.sent_messages_in_percent < 80
                  ? 'primary'
                  : 'warning'
              "
              :model-value="item.mailbox.sent_messages_in_percent"
            />
            <span v-else>
              {{ $gettext('Sending forbidden') }}
            </span>
          </template>
          <template v-else>
            {{ $gettext('Unlimited') }}
          </template>
        </template>
        <template v-else>
          {{ $gettext('No mailbox') }}
        </template>
      </template>
      <template #[`item.actions`]="{ item }">
        <template
          v-if="
            item.possible_actions !== undefined &&
            item.possible_actions.length !== 0
          "
        >
          <v-icon size="large" color="blue">mdi-circle-small</v-icon>
        </template>
        <v-menu location="bottom">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="small"
              icon="mdi-dots-horizontal"
              variant="text"
            >
            </v-btn>
          </template>
          <MenuItems :items="getMenuItems(item)" :obj="item" />
        </v-menu>
      </template>
    </v-data-table-server>
    <ConfirmDialog ref="confirmAlias" />
    <ConfirmDialog ref="confirmAccount">
      <v-checkbox
        v-model="keepAccountFolder"
        :label="$gettext('Do not delete account folder')"
        hide-details
      />
    </ConfirmDialog>
    <v-dialog v-model="showColumnsForm" max-width="500">
      <ChooseColumnsForm
        :columns="columns"
        :available-columns="currentAvailableColumns"
        :mandatory-columns="mandatoryColumns"
        @apply="updateDisplayedColumns"
      />
    </v-dialog>
  </v-card>
</template>

<script setup lang="js">
import { ref, onMounted, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import MenuItems from '@/components/tools/MenuItems.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import ChooseColumnsForm from '@/components/tools/ChooseColumnsForm.vue'
import { useRouter } from 'vue-router'
import { useBusStore } from '@/stores'
import accountsApi from '@/api/accounts'
import aliasesApi from '@/api/aliases'
import debounce from 'debounce'

const { $gettext } = useGettext()
const router = useRouter()
const { displayNotification } = useBusStore()

const availableAliasesColumns = {
  address: { title: $gettext('Address'), key: 'address' },
  enabled: { title: $gettext('Enabled'), key: 'enabled' },
  recipients: {
    title: $gettext('Recipients'),
    key: 'recipients',
  },
  expire_at: {
    title: $gettext('Expire at'),
    key: 'expire_at',
  },
  description: {
    title: $gettext('Description'),
    key: 'description',
  },
  creation: {
    title: $gettext('Creation date'),
    key: 'creation',
  },
  last_modification: {
    title: $gettext('Last modification'),
    key: 'last_modification',
  },
}

const defaultAliasColumns = [
  availableAliasesColumns.address,
  availableAliasesColumns.enabled,
  availableAliasesColumns.recipients,
]

const availableAccountsColumns = {
  username: { title: $gettext('Name'), key: 'username' },
  first_name: {
    title: $gettext('First name'),
    key: 'first_name',
  },
  last_name: {
    title: $gettext('Last Name'),
    key: 'last_name',
  },
  is_active: { title: $gettext('Enabled'), key: 'is_active' },
  role: { title: $gettext('Role'), key: 'role' },
  quota: { title: $gettext('Quota'), key: 'quota_usage' },
  message_limit: {
    title: $gettext('Message limit'),
    key: 'sent_messages_in_percent',
  },
  language: { title: $gettext('Language'), key: 'language' },
  phone_number: {
    title: $gettext('Phone number'),
    key: 'phone_number',
  },
  secondary_email: {
    title: $gettext('Secondary email'),
    key: 'secondary_email',
  },
  tfa_enabled: {
    title: $gettext('TFA enabled'),
    key: 'tfa_enabled',
  },
  totp_enabled: {
    title: $gettext('TOTP enabled'),
    key: 'totp_enabled',
  },
  webauth_enabled: {
    title: $gettext('WebAutn enabled'),
    key: 'webauth_enabled',
  },
  date_joined: {
    title: $gettext('Creation date'),
    key: 'date_joined',
  },
  last_login: {
    title: $gettext('Last login'),
    key: 'last_login',
  },
}

const defaultAccountsColumns = [
  availableAccountsColumns.username,
  availableAccountsColumns.is_active,
  availableAccountsColumns.role,
  availableAccountsColumns.quota,
]

const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' },
]

const identityType = ref('account')
const totalIdentities = ref(0)
const identities = ref([])
const loading = ref(false)
const search = ref('')
const selected = ref([])
const keepAccountFolder = ref(false)
const confirmAlias = ref()
const confirmAccount = ref()
const currentPage = ref(1)
const itemsPerPageR = ref(10)
const sortByR = ref([])
const columns = ref(defaultAccountsColumns)
const showColumnsForm = ref(false)

const headers = computed(() => {
  const result = columns.value
  return result.concat([
    {
      title: $gettext('Actions'),
      key: 'actions',
      sortable: false,
      align: 'end',
    },
  ])
})

const currentAvailableColumns = computed(() => {
  if (identityType.value === 'account') {
    return Object.values(availableAccountsColumns)
  } else {
    return Object.values(availableAliasesColumns)
  }
})

const mandatoryColumns = computed(() => {
  if (identityType.value === 'account') {
    return ['username']
  }
  return ['address']
})

async function updateType(value) {
  loading.value = true
  identities.value = []
  sortByR.value = []
  if (value === 'account') {
    columns.value = defaultAccountsColumns
  } else {
    columns.value = defaultAliasColumns
  }
  await fetchIdentities()
}

async function updatedOptions({ page, itemsPerPage, sortBy }) {
  currentPage.value = page
  itemsPerPageR.value = itemsPerPage
  sortByR.value = sortBy
  fetchIdentities()
}

async function fetchIdentities() {
  loading.value = true
  const params = {
    page: currentPage.value || 1,
    page_size: itemsPerPageR.value || 10,
  }
  if (sortByR.value && sortByR.value.length) {
    params.ordering = sortByR.value
      .map((item) => (item.order !== 'asc' ? `-${item.key}` : item.key))
      .join(',')
  }
  if (search.value !== '') {
    params.search = search.value
  }
  try {
    const resp =
      identityType.value === 'account'
        ? await accountsApi.getAll(params)
        : await aliasesApi.getAll(params)
    identities.value = resp.data.results
    totalIdentities.value = resp.data.count
    selected.value = []
  } finally {
    loading.value = false
  }
}

function updateDisplayedColumns(selection) {
  columns.value = currentAvailableColumns.value.filter((col) =>
    selection.includes(col.key)
  )
  showColumnsForm.value = false
}

function getMenuItems(item) {
  const result = []
  if (identityType.value === 'account') {
    item.possible_actions.forEach((element) => {
      result.push({
        label: element.label,
        icon: element.icon,
        onClick: (account) => {
          if (element.name === 'get_credentials') {
            downloadCredentials(account)
          }
          fetchIdentities()
        },
      })
    })
    result.push({
      label: $gettext('Edit'),
      icon: 'mdi-circle-edit-outline',
      onClick: editAccount,
    })
    result.push({
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteAccount,
      color: 'red',
    })
  } else if (identityType.value === 'alias') {
    result.push({
      label: $gettext('Edit'),
      icon: 'mdi-circle-edit-outline',
      onClick: editAlias,
    })
    result.push({
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteAlias,
      color: 'red',
    })
  }
  return result
}

function getActionMenuItems() {
  const result = []
  if (selected.value.length > 0) {
    result.push({
      label: $gettext('Delete'),
      icon: 'mdi-delete-outline',
      onClick: deleteIdentities,
      color: 'red',
    })
  }
  return result
}

function editAccount(account) {
  router.push({ name: 'AccountEdit', params: { id: account.pk } })
}

async function deleteAccount(account) {
  const result = await confirmAccount.value.open(
    $gettext('Warning'),
    $gettext('Are you sure you want to delete this identity ?'),
    {
      color: 'error',
      agreeLabel: $gettext('Yes'),
      cancelLabel: $gettext('No'),
    }
  )
  if (!result) {
    return
  }

  loading.value = false
  try {
    await accountsApi.delete(account.pk, { keepdir: keepAccountFolder.value })
    fetchIdentities()
    displayNotification({ msg: $gettext('Account deleted') })
  } finally {
    loading.value = false
  }
}

async function downloadCredentials(account) {
  const resp = await accountsApi.getCredentials(account.pk)
  const blob = new Blob([resp.data], { type: resp.headers['Content-Type'] })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `credentials_${account.pk}.pdf`
  link.click()
  URL.revokeObjectURL(link.href)
}

function editAlias() {}

function deleteIdentities() {}

async function deleteAlias(alias) {
  const result = await confirmAlias.value.open(
    $gettext('Warning'),
    $gettext('Are you sure you want to delete this alias?'),
    {
      color: 'error',
      agreeLabel: $gettext('Yes'),
      cancelLabel: $gettext('No'),
    }
  )
  if (!result) {
    return
  }
  loading.value = false
  try {
    await aliasesApi.delete(alias.pk)
    fetchIdentities()
    displayNotification({ msg: $gettext('Alias deleted') })
  } finally {
    loading.value = false
  }
}

function displayRecipients(alias) {
  if (!alias.recipients) {
    return ''
  }
  return alias.recipients.join(', ')
}

onMounted(() => {
  fetchIdentities()
})

defineExpose({
  fetchIdentities,
})

fetchIdentities = debounce(fetchIdentities, 500)
</script>

<style scoped lang="scss">
a {
  text-decoration: none;
  color: rgb(var(--v-theme-primary));

  &:visited {
    color: rgb(var(--v-theme-primary));
  }
}
</style>
