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
    class="ml-4"
    @click="showCreationForm = true"
    :title="$gettext('Add filter set')"
  />
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
         <MenuItems :items="filterActions" :obj="item" />
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
import accountApi from '@/api/account'
import FilterSetForm from '@/components/account/FilterSetForm.vue'
import FilterForm from '@/components/account/FilterForm.vue'
import MenuItems from '@/components/tools/MenuItems.vue'

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
  accountApi.getFilters(value.name).then(resp => {
    filters.value = resp.data
  })
})

function closeFilterSetForm() {
  showFilterSetForm.value = false
  fetchFilterSets()
}

function closeFilterForm() {
  showFilterForm.value = false
  selectedFilter.value = null
}

function fetchFilterSets() {
  accountApi.getFilterSets().then(resp => {
    filterSets.value = resp.data
  })
}

function editFilter(filter) {
  selectedFilter.value = filter
  showFilterForm.value = true
}

function deleteFilter(filter) {
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
