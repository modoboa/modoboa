<template>
  <div class="pa-4">
    <div class="text-h6 font-weight-regular mb-4">{{ $gettext('Message filters') }}</div>

    <v-toolbar dense floating color="white">
      <v-autocomplete
        v-model="currentFilterSet"
        :label="$gettext('Select a filter set')"
        :items="filterSets"
        :item-title="getFilterSetName"
        return-object
        variant="outlined"
        hide-details
        class="flex-grow-0"
        style="width: 200px"
        density="compact"
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
            icon="mdi-dots-vertical"
            v-bind="props"
            size="small"
            color="default"
          >
          </v-btn>
        </template>
        <MenuItems
          :items="getFilterSetActions()"
          :obj="currentFilterSet"
        />
      </v-menu>

      <v-switch
        v-if="currentFilterSet"
        v-model="rawMode"
        :label="$gettext('Raw mode')"
        color="primary"
        class="ml-4"
        hide-details
      />
    </v-toolbar>

    <div
      v-if="currentFilterSet"
      class="bg-white mt-4 pa-2"
    >
      <template v-if="!rawMode">
        <div class="d-flex align-center">
          <v-btn
            color="primary"
            :title="$gettext('Add new filter')"
            @click="showFilterForm = true"
            class="mx-auto"
          >
            <v-icon icon="mdi-plus" />
            {{ $gettext('Add') }}
          </v-btn>
        </div>
        <v-data-table
          :headers="headers"
          :items="filters"
          :loading="loadingFilters"
        >
          <template #[`item.enabled`]="{ item }">
            {{ $yesno(item.enabled) }}
          </template>
          <template #[`item.filter_actions`]="{ index, item }">
            <v-menu offset-y>
              <template #activator="{ props }">
                <v-btn
                  icon="mdi-dots-horizontal"
                  variant="text"
                  v-bind="props"
                >
                </v-btn>
              </template>
              <MenuItems :items="getFilterActions(item, index)" :obj="item" />
            </v-menu>
          </template>
        </v-data-table>
      </template>
      <template v-else>
        <v-form ref="rawFormRef">
          <v-textarea
            v-model="filterSetRawContent"
            variant="outlined"
            auto-grow
            :rules="[rules.required]"
            :error-messages="rawContentErrors"
          />
        </v-form>
        <v-btn
          color="success"
          @click="saveFilterSet"
          :loading="saving"
          class="mt-2"
        >
          {{ $gettext('Save') }}
        </v-btn>
      </template>
    </div>
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
import { useRoute, useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import rules from '@/plugins/rules'
import accountApi from '@/api/account'
import FilterSetForm from '@/components/account/FilterSetForm.vue'
import FilterForm from '@/components/account/FilterForm.vue'
import MenuItems from '@/components/tools/MenuItems.vue'

const router = useRouter()
const route = useRoute()
const busStore = useBusStore()
const { $gettext } = useGettext()

const filterSets = ref([])
const filters = ref([])
const filterSetRawContent = ref('')
const currentFilterSet = ref()
const loadingFilters = ref(false)
const rawContentErrors = ref([])
const rawFormRef = ref()
const rawMode = ref(false)
const saving = ref(false)
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
    if (route.params.filterset !== value.name) {
      router.push({
        name: 'AccountFilters', params: { filterset: value.name }
      })
    }
  } else {
    router.push({ name: 'AccountFilters' })
  }
})

watch(rawMode, (value) => {
  if (value) {
    accountApi.downloadFilterSet(currentFilterSet.value.name).then(resp => {
      filterSetRawContent.value = resp.data
    })
  } else {
    fetchFilters(currentFilterSet.value.name)
  }
})

watch(filterSetRawContent, () => {
  if (rawContentErrors.value.length) {
    rawContentErrors.value = []
  }
})

function getFilterSetName(filterSet) {
  let result = filterSet.name
  if (filterSet.active) {
    result += ' (' + $gettext('active') + ')'
  }
  else {
    result += ' (' + $gettext('inactive') + ')'
  }
  return result
}

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
    if (resp.data.length > 0 && resp.data[0].active && resp.data[0].name === null) {
      // No filter is active
      filterSets.value = resp.data.slice(1)
    } else {
      filterSets.value = resp.data
    }
    if (!currentFilterSet.value && route.params.filterset) {
      for (const filterSet of filterSets.value) {
        if (filterSet.name === route.params.filterset) {
          currentFilterSet.value = filterSet
          break
        }
      }
    }
  })
}

function fetchFilters(filterSetName) {
  loadingFilters.value = true
  accountApi.getFilters(filterSetName).then(resp => {
    filters.value = resp.data
    loadingFilters.value = false
  }).catch(error => {
    if (error.response.status === 518) { // Server is a teapot (sieve file contains custom code or is broken)
      // Let the user see with rawmode
      rawMode.value = true
      busStore.displayNotification({ msg: $gettext('Failed to display template. Using raw mode'), type: 'warning' })
    }
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

async function moveFilterDown(filter) {
  await accountApi.moveFilterDown(currentFilterSet.value.name, filter.name)
  fetchFilters(currentFilterSet.value.name)
}

async function moveFilterUp(filter) {
  await accountApi.moveFilterUp(currentFilterSet.value.name, filter.name)
  fetchFilters(currentFilterSet.value.name)
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

async function saveFilterSet() {
  const { valid } = await rawFormRef.value.validate()
  if (!valid) {
    return
  }
  const data = { content: filterSetRawContent.value }
  saving.value = true
  try {
    await accountApi.saveFilterSet(currentFilterSet.value.name, data)
    busStore.displayNotification({ msg: $gettext('Filter set updated') })
  } catch (err) {
    if (err.response.status === 400 && err.response.data.content) {
      rawContentErrors.value = err.response.data.content
    }
  } finally {
    saving.value = false
  }
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

function getFilterActions(filter, index) {
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
  if (index !== filters.value.length - 1) {
    result.push({
      label: $gettext('Move down'),
      icon: 'mdi-arrow-down',
      onClick: moveFilterDown
    })
  }
  if (index !== 0) {
    result.push({
      label: $gettext('Move up'),
      icon: 'mdi-arrow-up',
      onClick: moveFilterUp
    })
  }
  return result
}

const filterSetActions = [
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
]

function getFilterSetActions() {
  const result = []
  if (!currentFilterSet.value.active) {
    result.push({
      label: $gettext('Activate filter set'),
      color: 'success',
      icon: 'mdi-check',
      onClick: activateFilterSet
    })
  }
  return result.concat(filterSetActions)
}

fetchFilterSets()
</script>
