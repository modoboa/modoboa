<template>
  <v-card class="mt-6">
    <v-data-table
      v-model="selected"
      v-model:expanded="expanded"
      :headers="headers"
      :items="Object.values(providers)"
      :search="search"
      :loading="!providersLoaded"
      item-value="name"
      single-expand
      show-select
      @click:row="(item, slot) => slot.expand(!slot.isExpanded)"
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
            @click="reloadProviders"
          ></v-btn>
          <v-spacer></v-spacer>
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            :placeholder="$gettext('Search')"
            single-line
            variant="outlined"
            hide-details
          />
        </v-toolbar>
      </template>

      <template #[`item.secured`]="{ item }">
        <v-icon v-if="item.secured === true" color="green"> mdi-lock </v-icon>
        <v-icon v-else color="red"> mdi-lock-off </v-icon>
      </template>
      <template #[`item.domains`]="{ item }">
        <v-chip v-if="item.domains.length > 0">
          {{ item.domains.length }} associated domain(s)
        </v-chip>
        <v-chip v-else> No associated domain </v-chip>
      </template>
      <template #[`expanded-item`]="{ headers, item }">
        <td :colspan="headers.length">
          <v-chip v-for="(domain, index) in item.domains" :key="index">
            <template v-if="domain.new_domain">
              {{ domain.name }} --> {{ domain.new_domain.name }}
            </template>
            <template v-else>
              {{ domain.name }} --> {{ domain.name }}
            </template>
          </v-chip>
        </td>
      </template>
      <template #[`item.actions`]="{ item }">
        <v-menu offset-y>
          <template #activator="{ props }">
            <v-btn icon="mdi-dots-horizontal" variant="text" v-bind="props" />
          </template>
          <MenuItems :items="getMenuItems()" :obj="item" />
        </v-menu>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup lang="js">
import { useProvidersStore } from '@/stores'
import MenuItems from '@/components/tools/MenuItems'
import { useGettext } from 'vue3-gettext'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const { $gettext } = useGettext()
const providersStore = useProvidersStore()
const router = useRouter()

const providers = computed(() => providersStore.providers)
const providersLoaded = computed(() => providersStore.providersLoaded)

const headers = [
  { title: $gettext('Name'), key: 'name' },
  { title: $gettext('Address'), key: 'address' },
  { title: $gettext('Port'), key: 'port' },
  { title: $gettext('Secured'), key: 'secured' },
  { title: $gettext('Associated domains'), key: 'domains' },
  {
    title: $gettext('Actions'),
    key: 'actions',
    sortable: false,
    align: 'right',
  },
]

const selected = ref([])
const search = ref('')
const expanded = ref([])

function deleteProvider(provider) {
  providersStore.deleteProvider(provider.id)
}

function editProvider(provider) {
  router.push({ name: 'ProviderEdit', params: { id: provider.id } })
}

function getMenuItems() {
  const result = []
  result.push({
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: deleteProvider,
    color: 'red',
  })
  result.push({
    label: $gettext('Edit'),
    icon: 'mdi-circle-edit-outline',
    onClick: editProvider,
  })
  return result
}

function reloadProviders() {
  providersStore.getProviders()
}

if (!providersLoaded.value) {
  reloadProviders()
}
</script>
