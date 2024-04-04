<template>
<v-toolbar flat>
  <v-toolbar-title>{{ $gettext('Message filters') }}</v-toolbar-title>
</v-toolbar>

<div class="d-flex bg-white align-center pa-4">
  <v-autocomplete
    v-model="currentFilterSet"
    :label="$gettext('Select a filter set')"
    :items="filterSets"
    item-title="name"
    return-object
    variant="outlined"
    hide-details
    class="flex-grow-0"
    style="width: 200px"
  />
  <v-btn
    color="primary"
    icon="mdi-plus"
    size="small"
    class="mx-4"
    @click="showFilterSetForm = true"
    :title="$gettext('Add filter set')"
  />
  <v-menu v-if="currentFilterSet">
    <template v-slot:activator="{ props }">
      <v-btn
        append-icon="mdi-chevron-down"
        v-bind="props"
        size="small"
        color="default"
      >
        {{ $gettext('Actions') }}
      </v-btn>
    </template>
    <MenuItems
      :items="filterSetActions"
      :obj="currentFilterSet"
      />
  </v-menu>
</div>

<div
  v-if="currentFilterSet"
  class="bg-white mt-4 pa-2"
>
  <div class="d-flex align-center">
    <v-spacer />
    <v-btn
      color="primary"
      :title="$gettext('Add new filter')"
      @click="showFilterForm = true"
    >
      <v-icon icon="mdi-plus" />
      {{ $gettext('Add') }}
    </v-btn>
  </div>
  <v-data-table
    :headers="headers"
    :items="filters"
  >
    <template #[`item.enabled`]="{ item }">
      {{ $yesno(item.enabled) }}
    </template>
    <template #[`item.filter_actions`]="{ item }">
       <v-menu offset-y>
         <template #activator="{ props }">
           <v-btn
             icon="mdi-dots-horizontal"
             variant="text"
             v-bind="props"
             >
           </v-btn>
         </template>
         <MenuItems :items="getFilterActions(item)" :obj="item" />
       </v-menu>
    </template>
  </v-data-table>
</div>

<v-dialog
  v-model="showFilterSetForm"
  max-width="600"
>
  <FilterSetForm
    @close="closeFilterSetForm"
  />
</v-dialog>

<v-dialog
  v-model="showFilterForm"
  max-width="800"
>
  <FilterForm
    v-if="currentFilterSet"
    :filter-set="currentFilterSet.name"
    :filter="selectedFilter"
    @close="closeFilterForm"
  />
</v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import accountApi from '@/api/account'
import FilterSetForm from '@/components/account/FilterSetForm.vue'
import FilterForm from '@/components/account/FilterForm.vue'
import MenuItems from '@/components/tools/MenuItems.vue'

const busStore = useBusStore()
const { $gettext } = useGettext()

const filterSets = ref([])
const filters = ref([])
const currentFilterSet = ref()
const selectedFilter = ref(null)
const showFilterSetForm = ref(false)
const showFilterForm = ref(false)

const headers = [
  { title: $gettext('Name'), key: 'name' },
  { title: $gettext('Active'), key: 'enabled' },
  { title: '', key: 'filter_actions', align: 'end' }
]

watch(currentFilterSet, (value) => {
  if (value) {
    fetchFilters(value.name)
  }
})

function closeFilterSetForm() {
  showFilterSetForm.value = false
  fetchFilterSets()
}

function closeFilterForm() {
  showFilterForm.value = false
  selectedFilter.value = null
  fetchFilters(currentFilterSet.value.name)
}

function fetchFilterSets() {
  accountApi.getFilterSets().then(resp => {
    filterSets.value = resp.data
  })
}

function fetchFilters(filterSetName) {
  accountApi.getFilters(filterSetName).then(resp => {
    filters.value = resp.data
  })
}

function editFilter(filter) {
  selectedFilter.value = filter
  showFilterForm.value = true
}

function enableFilter(filter) {
  accountApi.enableFilter(currentFilterSet.value.name, filter.name).then(() => {
    filter.enabled = true
    busStore.displayNotification({ msg: $gettext('Filter enabled') })
  })
}

function disableFilter(filter) {
  accountApi.disableFilter(currentFilterSet.value.name, filter.name).then(() => {
    filter.enabled = false
    busStore.displayNotification({ msg: $gettext('Filter disabled') })
  })
}

function deleteFilter(filter) {
  accountApi.deleteFilter(currentFilterSet.value.name, filter.name).then(() => {
    busStore.displayNotification({ msg: $gettext('Filter removed') })
    fetchFilters(currentFilterSet.value.name)
  })
}

async function activateFilterSet(filterSet) {
  await accountApi.activateFilterSet(filterSet.name)
  busStore.displayNotification({ msg: $gettext('Filter set activated') })
}

async function deleteFilterSet(filterSet) {
  await accountApi.deleteFilterSet(filterSet.name)
  busStore.displayNotification({ msg: $gettext('Filter set removed') })
  currentFilterSet.value = null
  fetchFilterSets()
}

async function downloadFilterSet(filterSet) {
  const resp = await accountApi.downloadFilterSet(filterSet.name)
  const blob = new Blob([resp.data], { type: 'text/plain' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${filterSet.name}.txt`
  link.click()
  URL.revokeObjectURL(link.href)
}

const filterActions = [
  {
    label: $gettext('Edit'),
    icon: 'mdi-circle-edit-outline',
    onClick: editFilter
  },
  {
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: deleteFilter,
    color: 'red'
  }
]

function getFilterActions(filter) {
  const result = [...filterActions]
  if (filter.enabled) {
    result.push({
      label: $gettext('Disable'),
      icon: 'mdi-stop',
      color: 'red',
      onClick: disableFilter
    })
  } else {
    result.push({
      label: $gettext('Enable'),
      icon: 'mdi-check',
      color: 'success',
      onClick: enableFilter
    })
  }
  return result
}

const filterSetActions = ref([
  {
    label: $gettext('Activate filter set'),
    color: 'success',
    icon: 'mdi-check',
    onClick: activateFilterSet
  },
  {
    label: $gettext('Download filter set'),
    icon: 'mdi-download',
    onClick: downloadFilterSet
  },
  {
    label: $gettext('Delete filter set'),
    color: 'error',
    icon: 'mdi-trash-can',
    onClick: deleteFilterSet
  }
])

fetchFilterSets()
</script>

<style scoped>
 .v-toolbar {
   background-color: #f7f8fa !important;
 }
 .v-tabs {
   background-color: #f7f8fa !important;
 }
</style>
