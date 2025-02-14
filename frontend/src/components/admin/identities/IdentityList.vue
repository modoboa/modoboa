<template>
  <v-card class="mt-6">
    <v-data-table
      v-model="selected"
      :headers="headers"
      :items="identities"
      :search="search"
      :loading="!identitiesLoaded"
      item-value="identity"
      class="elevation-0"
      show-select
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
          <v-spacer></v-spacer>
        </v-toolbar>
      </template>
      <template #[`item.identity`]="{ item }">
        <template v-if="item.type === 'account'">
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
          <v-icon size="2.5em" color="blue">mdi-circle-small</v-icon>
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
    </v-data-table>
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
import { ref, computed, onMounted } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useIdentitiesStore } from '@/stores'
import MenuItems from '@/components/tools/MenuItems.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useRouter } from 'vue-router'

const { $gettext } = useGettext()
const identitiesStore = useIdentitiesStore()
const router = useRouter()

const headers = ref([
  { title: $gettext('Name'), key: 'identity' },
  { title: $gettext('Fullname/recipient'), key: 'name_or_rcpt' },
  { title: $gettext('Tags'), key: 'tags' },
  {
    title: $gettext('Actions'),
    key: 'actions',
    sortable: false,
    align: 'end',
  },
])

const identities = computed(() => identitiesStore.identities)
const identitiesLoaded = computed(() => identitiesStore.identitiesLoaded)
const search = ref('')
const selected = ref([])
const keepAccountFolder = ref(false)
const confirmAlias = ref()
const confirmAccount = ref()

function fetchIdentities() {
  identitiesStore.getIdentities().then(() => {
    selected.value = []
  })
}

function getMenuItems(item) {
  const result = []
  if (item.type === 'account') {
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
  } else if (item.type === 'alias') {
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
  identitiesStore
    .deleteIdentity(account.type, account.pk, {
      keepdir: keepAccountFolder.value,
    })
    .then(() => {
      keepAccountFolder.value = false
    })
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
  identitiesStore.deleteIdentity(alias.type, alias.pk)
}

onMounted(() => {
  if (identities.value.length < 1) {
    fetchIdentities()
  }
})
</script>
