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
      item-value="key"
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
          <v-menu location="bottom">
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
          <v-radio-group
            v-model="identityType"
            inline
            @update:model-value="updateType"
            :readonly="loading"
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
          <v-combobox
            v-model="columns"
            :items="currentAvailableColumns"
            multiple
            return-object
          >
          </v-combobox>
          <v-spacer></v-spacer>
        </v-toolbar>
      </template>
      <template #[`item.identity`]="{ item }">
        <template v-if="identityType === 'account'">
          <router-link :to="{ name: 'AccountDetail', params: { id: item.pk } }">
            {{ item.identity }}
          </router-link>
        </template>
        <template v-else>
          <router-link :to="{ name: 'AliasDetail', params: { id: item.pk } }">
            {{ item.identity }}
          </router-link>
        </template>
      </template>
      <template #[`item.enabled`]="{ item }">
        <v-icon
          :color="item.enabled ? 'success' : 'error'"
          :icon="item.enabled ? 'mdi-check-circle' : 'mdi-close-circle'"
          variant="flat"
        />
      </template>
      <template #[`item.tags`]="{ item }">
        <v-chip
          v-for="(tag, index) in item.tags"
          :key="tag.name"
          :color="tag.type !== 'idt' ? 'primary' : 'default'"
          :class="index > 0 ? 'ml-2' : ''"
          size="small"
        >
          {{ tag.label }}
        </v-chip>
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
  </v-card>
</template>

<script setup lang="js">
import { ref, onMounted, computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import MenuItems from '@/components/tools/MenuItems.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useRouter } from 'vue-router'
import { useBusStore } from '@/stores'
import accountsApi from '@/api/accounts'
import aliasesApi from '@/api/aliases'
import debounce from 'debounce'
// import identitiesApi from '@/api/identities'

const { $gettext, $pgettext } = useGettext()
const router = useRouter()
const { displayNotification } = useBusStore()

const availableAliasesColumns = {
  address: { title: $gettext('Address'), key: 'address', value: 'address' },
  enabled: { title: $gettext('Enabled'), key: 'enabled', value: 'enabled' },
  recipients: {
    title: $gettext('Recipients'),
    key: 'recipients',
    value: 'recipients',
  },
  expire_at: {
    title: $gettext('Expire at'),
    key: 'expire_at',
    value: 'expire_at',
  },
  description: {
    title: $gettext('Description'),
    key: 'description',
    value: 'description',
  },
  creation: {
    title: $gettext('Creation date'),
    key: 'creation',
    value: 'creation',
  },
  last_modification: {
    title: $gettext('Last modification'),
    key: 'last_modification',
    value: 'last_modification',
  },
}

const defaultAliasColumns = [
  availableAliasesColumns.address,
  availableAliasesColumns.enabled,
  availableAliasesColumns.recipients,
]

const availableAccountsColumns = {
  username: { title: $gettext('Name'), key: 'username', value: 'username' },
  first_name: {
    title: $gettext('First name'),
    key: 'first_name',
    value: 'first_name',
  },
  last_name: {
    title: $gettext('Last Name'),
    key: 'last_name',
    value: 'last_name',
  },
  is_active: { title: $gettext('Enabled'), key: 'enabled', value: 'is_active' },
  role: { title: $gettext('Role'), key: 'role', value: 'role' },
  language: { title: $gettext('Language'), key: 'language', value: 'language' },
  phone_number: {
    title: $gettext('Phone number'),
    key: 'phone_number',
    value: 'phone_number',
  },
  secondary_email: {
    title: $gettext('Secondary email'),
    key: 'secondary_email',
    value: 'secondary_email',
  },
  tfa_enabled: {
    title: $gettext('TFA enabled'),
    key: 'tfa_enabled',
    value: 'tfa_enabled',
  },
  totp_enabled: {
    title: $gettext('TOTP enabled'),
    key: 'totp_enabled',
    value: 'totp_enabled',
  },
  webauth_enabled: {
    title: $gettext('WebAutn enabled'),
    key: 'webauth_enabled',
    value: 'webauth_enabled',
  },
  date_joined: {
    title: $gettext('Created date'),
    key: 'date_joined',
    value: 'date_joined',
  },
  last_login: {
    title: $gettext('Last login'),
    key: 'last_login',
    value: 'last_login',
  },
}

const defaultAccountsColumns = [
  availableAccountsColumns.username,
  availableAccountsColumns.is_active,
  availableAccountsColumns.role,
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

async function updateType(value) {
  loading.value = true
  sortByR.value = []
  if (value === 'account') {
    columns.value = defaultAccountsColumns
  } else {
    columns.value = defaultAliasColumns
  }
  fetchIdentities()
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
        ? await accountsApi.getAllParams(params)
        : await aliasesApi.getAll(params)
    identities.value = resp.data.results
    totalIdentities.value = resp.data.count
    selected.value = []
  } finally {
    loading.value = false
  }
}

function getMenuItems(item) {
  const result = []
  if (identityType === 'account') {
    item.possible_actions.forEach((element) => {
      result.push({
        label: element.label,
        icon: element.icon,
        onClick: () => {
          if (element.type === 'download') {
            //TODO : downloadFile(element)
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
  } else if (identityType === 'alias') {
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

onMounted(() => {
  fetchIdentities()
})

defineExpose({
  fetchIdentities,
})

fetchIdentities = debounce(fetchIdentities, 500)
</script>
