<template>
  <div>
    <v-card class="mt-6">
      <v-data-table-server
        :headers="headers"
        :items="contacts"
        :items-length="totalContacts"
        :loading="loading"
        :search="search"
        item-value="pk"
        show-expand
        @update:options="fetchContacts"
      >
        <template #top>
          <v-toolbar color="white" flat>
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              :placeholder="$gettext('Search')"
              variant="outlined"
              single-line
              flat
              hide-details
              density="compact"
              class="flex-grow-0 w-33 mr-4"
            ></v-text-field>
            <v-btn color="primary" variant="outlined" @click="showForm = true">
              {{ $gettext('Add') }}
            </v-btn>
            <template v-if="preferences.enable_carddav_sync">
              <v-btn class="ml-2" variant="tonal" icon size="small">
                <v-icon icon="mdi-cog" />
                <v-menu activator="parent">
                  <v-list density="compact">
                    <v-list-item
                      v-if="!addressBook.last_sync"
                      color="success"
                      :title="
                        $gettext('Synchronize contacts with address book')
                      "
                      prepend-icon="mdi-sync"
                      @click="syncToAddressBook"
                    />
                    <v-list-item
                      :title="$gettext('Synchronize')"
                      prepend-icon="mdi-sync"
                      :disabled="addressBook.syncing"
                      @click="syncFromAddressBook(true)"
                    />
                  </v-list>
                </v-menu>
              </v-btn>
              <v-btn
                icon="mdi-information-outline"
                :title="$gettext('Display address book information')"
                @click="showAddressBookInfo = true"
              />
            </template>
            <v-chip
              v-if="$route.params.category"
              class="my-2 mx-4"
              label
              size="small"
              color="green"
              prepend-icon="mdi-label"
              @click="editCategory"
            >
              {{ $route.params.category }}
            </v-chip>
            <v-spacer></v-spacer>
            <v-progress-circular
              v-if="addressBook.syncing"
              color="primary"
              indeterminate
            ></v-progress-circular>
          </v-toolbar>
        </template>
        <template
          #[`item.data-table-expand`]="{
            internalItem,
            isExpanded,
            toggleExpand,
          }"
        >
          <v-btn
            :append-icon="
              isExpanded(internalItem) ? 'mdi-chevron-up' : 'mdi-chevron-down'
            "
            :text="isExpanded(internalItem) ? 'Collapse' : 'More info'"
            class="text-none"
            color="medium-emphasis"
            size="small"
            variant="text"
            width="105"
            border
            slim
            @click="toggleExpand(internalItem)"
          ></v-btn>
        </template>
        <template #[`item.actions`]="{ item }">
          <div class="text-right">
            <v-menu offset-y>
              <template #activator="{ props }">
                <v-btn icon="mdi-dots-horizontal" variant="text" v-bind="props">
                </v-btn>
              </template>
              <MenuItems :items="contactActions" :obj="item" />
            </v-menu>
          </div>
        </template>
        <template #expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length" class="pa-4">
              <v-card v-if="item.emails.length" class="mb-4">
                <v-card-title class="bg-surface-light">
                  <v-icon icon="mdi-email" class="mr-4"></v-icon
                  >{{ $gettext('Email addresses') }}
                </v-card-title>
                <v-card-text class="pt-4">
                  <v-row v-for="email in item.emails" :key="email" class="mt-2">
                    <v-col cols="2">
                      <v-chip size="small" color="info">{{
                        email.type
                      }}</v-chip>
                    </v-col>
                    <v-col cols="10">
                      {{ email.address }}
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
              <v-card v-if="item.phone_numbers.length" class="mb-4">
                <v-card-title class="bg-surface-light">
                  <v-icon icon="mdi-phone" class="mr-4"></v-icon
                  >{{ $gettext('Phone numbers') }}
                </v-card-title>
                <v-card-text class="pt-4">
                  <v-row
                    v-for="number in item.phone_numbers"
                    :key="number"
                    class="mt-2"
                  >
                    <v-col cols="2">
                      <v-chip size="small" color="info">{{
                        number.type
                      }}</v-chip>
                    </v-col>
                    <v-col cols="10">
                      {{ number.number }}
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </td>
          </tr>
        </template>
      </v-data-table-server>
    </v-card>
    <v-dialog v-model="showForm" persistent max-width="800px">
      <ContactForm
        :contact="selectedContact"
        @close="closeForm"
        @added="fetchContacts"
        @updated="fetchContacts"
      />
    </v-dialog>
    <v-dialog v-model="showCategoriesForm" persistent max-width="800px">
      <ContactCategoriesForm
        :contact="selectedContact"
        @updated="fetchContacts"
        @close="closeCategoriesForm"
      />
    </v-dialog>
    <v-dialog v-model="showAddressBookInfo" persistent max-width="800px">
      <AddressBookInfo
        :address-book-url="addressBook.url"
        @close="showAddressBookInfo = false"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useBusStore } from '@/stores'
import contactsApi from '@/api/contacts'
import parametersApi from '@/api/parameters'
import AddressBookInfo from './AddressBookInfo.vue'
import ContactForm from './ContactForm.vue'
import ContactCategoriesForm from './ContactCategoriesForm.vue'
import MenuItems from '@/components/tools/MenuItems'

const emit = defineEmits(['editCategory'])

const route = useRoute()
const { $gettext } = useGettext()
const { displayNotification } = useBusStore()

const addressBook = ref({})
const contacts = ref([])
const totalContacts = ref(0)
const search = ref('')
const selectedContact = ref(null)
const showAddressBookInfo = ref(false)
const showForm = ref(false)
const showCategoriesForm = ref(false)
const preferences = ref({})
const loading = ref(false)

const headers = [
  { key: 'first_name', title: $gettext('First name') },
  { key: 'last_name', title: $gettext('Last name') },
  { width: 1, key: 'data-table-expand' },
  { key: 'actions', title: $gettext('Actions'), align: 'end', sortable: false },
]

const contactActions = [
  {
    label: $gettext('Categories'),
    icon: 'mdi-label',
    onClick: editCategories,
  },
  {
    label: $gettext('Edit'),
    icon: 'mdi-circle-edit-outline',
    onClick: editContact,
  },
  {
    label: $gettext('Delete'),
    icon: 'mdi-delete-outline',
    onClick: deleteContact,
    color: 'red',
  },
]

let intervalId

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})

function closeForm() {
  showForm.value = false
  selectedContact.value = null
}

function displayEmails(emails) {
  return emails.map((email) => email.address).join(', ')
}

function editContact(contact) {
  selectedContact.value = contact
  showForm.value = true
}

function editCategory() {
  emit('editCategory')
}

function editCategories(contact) {
  selectedContact.value = contact
  showCategoriesForm.value = true
}

function closeCategoriesForm() {
  showCategoriesForm.value = false
  selectedContact.value = null
}

function deleteContact(contact) {
  contactsApi.deleteContact(contact.pk).then(() => {
    fetchContacts()
  })
}

async function fetchAddressBook() {
  const resp = await contactsApi.getDefaultAddressBook()
  addressBook.value = resp.data
}

async function fetchPreferences() {
  const resp = await parametersApi.getUserApplication('contacts')
  preferences.value = resp.data.params
}

async function fetchContacts(options) {
  const params = {
    page: options?.page || 1,
    page_size: options?.itemsPerPage || 10,
    ...route.params,
  }
  if (options?.sortBy) {
    params.ordering = options.sortBy
      .map((item) => (item.order !== 'asc' ? `-${item.key}` : item.key))
      .join(',')
  }
  if (search.value !== '') {
    params.search = search.value
  }
  loading.value = true
  try {
    const resp = await contactsApi.getContacts(params)
    contacts.value = resp.data.results
    totalContacts.value = resp.data.count
  } finally {
    loading.value = false
  }
}

function syncToAddressBook() {
  contactsApi.synchronizeToAddressBook().then(() => {
    displayNotification({ msg: $gettext('Synchronization started') })
  })
}

async function monitorAddressBook() {
  await fetchAddressBook()
  await fetchContacts()
  if (!addressBook.value.syncing) {
    clearInterval(intervalId)
    intervalId = null
    startAutomaticSync()
  }
}

async function syncFromAddressBook(withNotification) {
  if (intervalId) {
    // Stop automatic sync for now.
    clearInterval(intervalId)
  }
  await contactsApi.synchronizeFromAddressBook()
  if (withNotification) {
    displayNotification({ msg: $gettext('Synchronization started') })
  }
  addressBook.value.syncing = true
  intervalId = setInterval(monitorAddressBook, 5000)
}

function startAutomaticSync() {
  intervalId = setInterval(
    syncFromAddressBook,
    preferences.value.sync_frequency * 1000
  )
}

await fetchAddressBook()
await fetchPreferences()

watch(preferences, (value) => {
  if (value) {
    startAutomaticSync()
  }
})

watch(
  () => route.params.category,
  () => {
    fetchContacts()
  }
)
</script>
