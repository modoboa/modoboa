<template>
  <v-card class="mt-6">
    <v-data-table :headers="headers" :items="contacts">
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

          <v-menu location="bottom">
            <template #activator>
              <v-btn
                color="primary"
                variant="outlined"
                @click="showForm = true"
              >
                {{ $gettext('Add') }}
              </v-btn>
            </template>
            <v-list density="compact"> </v-list>
          </v-menu>
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
        </v-toolbar>
      </template>
      <template #[`item.emails`]="{ item }">
        {{ displayEmails(item.emails) }}
      </template>
      <template #[`item.phone_numbers`]="{ item }">
        {{ displayPhoneNumbers(item.phone_numbers) }}
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
    </v-data-table>
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
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import contactsApi from '@/api/contacts'
import ContactForm from './ContactForm.vue'
import ContactCategoriesForm from './ContactCategoriesForm.vue'
import MenuItems from '@/components/tools/MenuItems'

const emit = defineEmits(['editCategory'])

const route = useRoute()
const { $gettext } = useGettext()

const contacts = ref([])
const search = ref('')
const selectedContact = ref(null)
const showForm = ref(false)
const showCategoriesForm = ref(false)

const headers = [
  { key: 'display_name', title: $gettext('Display name') },
  { key: 'emails', title: $gettext('E-mail') },
  { key: 'phone_numbers', title: $gettext('Phone') },
  { key: 'actions', title: $gettext('Actions'), align: 'end' },
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

function closeForm() {
  showForm.value = false
  selectedContact.value = null
}

function displayEmails(emails) {
  return emails.map((email) => email.address).join(', ')
}

function displayPhoneNumbers(phoneNumbers) {
  return phoneNumbers.map((phoneNumber) => phoneNumber.number).join(', ')
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
  selectedContact.value = false
}

function deleteContact(contact) {
  contactsApi.deleteContact(contact.pk).then(() => {
    fetchContacts()
  })
}

function fetchContacts() {
  contactsApi.getContacts(route.params).then((resp) => {
    contacts.value = resp.data
  })
}

fetchContacts()

watch(
  () => route.params.category,
  () => {
    fetchContacts()
  }
)
</script>
