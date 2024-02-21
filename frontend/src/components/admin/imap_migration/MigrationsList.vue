<template>
  <v-card class="mt-6">
    <v-data-table
      v-model="selected"
      v-model:options="options"
      :headers="headers"
      :items="migrations"
      :search="search"
      :server-items-length="totalMigrations"
      :loading="loading"
      show-select
    >
      <template #top>
        <v-toolbar color="white" flat>
          <v-menu location="bottom">
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                variant="flat"
                append-icon="mdi-chevron-down"
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
            @click="getMigrations()"
          ></v-btn>
          <v-spacer></v-spacer>
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            placeholder="Search"
            filled
            variant="outlined"
            density="compact"
            hide-details
          ></v-text-field>
        </v-toolbar>
      </template>
      <template #[`item.mailbox`]="{ item }">
        <router-link
          :to="{
            name: 'AccountDetail',
            params: { id: item.mailbox.user },
          }"
        >
          {{ item.mailbox.full_address }}
        </router-link>
      </template>
      <template #[`item.actions`]="{ item }">
        <v-menu offset-y>
          <template #activator="{ props }">
            <v-btn icon="mdi-dots-horizontal" v-bind="props" />
          </template>
          <MenuItems :items="getMenuItems()" :object="item" />
        </v-menu>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup lang="js">
import migrationApi from '@/api/imap_migration/migrations'
import MenuItems from '@/components/tools/MenuItems'
import { useBusStore } from '@/stores'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
const busStore = useBusStore()

const migrations = ref([])
const headers = [
  { title: $gettext('Provider'), value: 'provider.name' },
  { title: $gettext('Old account'), value: 'username' },
  { title: $gettext('New account'), value: 'mailbox' },
  {
    title: $gettext('Actions'),
    value: 'actions',
    sortable: false,
    align: 'right',
  },
]

const selected = ref([])
const loading = ref(false)
const search = ref('')
const options = ref({})
const totalMigrations = ref(0)

function deleteMigration(migration) {
  migrationApi.deleteMigration(migration.id).then(() => {
    busStore.displayNotification({ msg: $gettext('Migration deleted') })
    migrations.value = migrations.value.filter((item) => {
      return item.id !== migration.id
    })
  })
}

function getMigrations(filter) {
  loading.value = true
  let query = {}
  if (filter !== undefined) {
    query = { params: { search: filter } }
  }
  migrationApi
    .getMigrations(query)
    .then((response) => {
      migrations.value = response.data
      totalMigrations.value = migrations.value.length
    })
    .finally(() => (loading.value = false))
}

function getMenuItems() {
  const result = []
  result.push({
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: deleteMigration(),
    color: 'red',
  })
  return result
}

getMigrations()
</script>
